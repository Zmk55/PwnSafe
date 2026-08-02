#!/usr/bin/env bash

set -Eeuo pipefail

restart_service=1
if [[ "${1:-}" == "--no-restart" ]]; then
    restart_service=0
    shift
fi
if (( $# )); then
    echo "Usage: $0 [--no-restart]" >&2
    exit 2
fi

if (( EUID != 0 )); then
    sudo_args=()
    (( restart_service == 0 )) && sudo_args+=(--no-restart)
    exec sudo bash "$0" "${sudo_args[@]}"
fi

log() {
    printf '[PwnSafe repair] %s\n' "$*"
}

if [[ -x /home/pi/.pwn/bin/python ]]; then
    python_bin=/home/pi/.pwn/bin/python
else
    python_bin=$(command -v python3 || true)
fi
if [[ -z "${python_bin:-}" ]]; then
    echo "Python 3 was not found." >&2
    exit 1
fi

package_root=$(
    "$python_bin" -c 'import os, pwnagotchi; print(os.path.dirname(os.path.realpath(pwnagotchi.__file__)))'
)
handler="$package_root/ui/web/handler.py"
template="$package_root/ui/web/templates/plugins.html"
enable_assoc=/usr/local/share/pwnagotchi/custom-plugins/enable_assoc.py
stamp=$(date +%Y%m%d-%H%M%S)

for required in "$handler" "$template"; do
    if [[ ! -f "$required" ]]; then
        echo "Required Pwnagotchi file not found: $required" >&2
        exit 1
    fi
done

font_works() {
    "$python_bin" - >/dev/null 2>&1 <<'PY'
from PIL import ImageFont
ImageFont.truetype("DejaVuSansMono-Oblique", 12)
PY
}

if font_works; then
    log "DejaVuSansMono-Oblique is already available."
else
    if ! command -v apt-get >/dev/null; then
        echo "The oblique font is missing and apt-get is unavailable." >&2
        exit 1
    fi
    log "Installing fonts-dejavu-extra."
    if dpkg-query -W -f='${Status}' fonts-dejavu-extra 2>/dev/null | grep -q 'install ok installed'; then
        install_args=(--reinstall -y fonts-dejavu-extra)
    else
        install_args=(-y fonts-dejavu-extra)
    fi
    if ! DEBIAN_FRONTEND=noninteractive apt-get install "${install_args[@]}"; then
        apt-get update
        DEBIAN_FRONTEND=noninteractive apt-get install "${install_args[@]}"
    fi
    font_works || { echo "Pillow still cannot load DejaVuSansMono-Oblique." >&2; exit 1; }
fi

if [[ -f "$enable_assoc" ]]; then
    "$python_bin" - "$enable_assoc" "$stamp" <<'PY'
import os
import pathlib
import shutil
import sys

path = pathlib.Path(sys.argv[1])
stamp = sys.argv[2]
text = path.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
final_call = "ui.set('assoc_count', str(self._count))"
broken_calls = {"ui.set('assoc_count')", "ui.set('assoc_count', self._count)"}

if any(line.strip() == final_call for line in lines):
    print("[PwnSafe repair] enable_assoc is already fixed.")
else:
    matches = [index for index, line in enumerate(lines) if line.strip() in broken_calls]
    if len(matches) != 1:
        raise SystemExit("Refusing to patch enable_assoc: expected exactly one recognized broken call.")
    index = matches[0]
    line = lines[index]
    indent = line[:len(line) - len(line.lstrip())]
    ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
    lines[index] = f"{indent}{final_call}{ending}"
    updated = "".join(lines)
    compile(updated, str(path), "exec")

    backup = path.with_name(f"{path.name}.pwnsafe-{stamp}.bak")
    shutil.copy2(path, backup)
    stat = path.stat()
    temporary = path.with_name(f"{path.name}.pwnsafe.tmp")
    temporary.write_text(updated, encoding="utf-8")
    os.chmod(temporary, stat.st_mode)
    os.chown(temporary, stat.st_uid, stat.st_gid)
    os.replace(temporary, path)
    print(f"[PwnSafe repair] Fixed enable_assoc; backup: {backup}")
PY
else
    log "enable_assoc is not installed; skipping its repair."
fi

"$python_bin" - "$handler" "$template" "$stamp" <<'PY'
import os
import pathlib
import shutil
import sys

handler_path = pathlib.Path(sys.argv[1])
template_path = pathlib.Path(sys.argv[2])
stamp = sys.argv[3]
original_handler = handler_path.read_text(encoding="utf-8")
original_template = template_path.read_text(encoding="utf-8")
handler = original_handler
template = original_template

helper = '''def _plugin_descriptions(database, loaded):
    descriptions = {}
    for name, filename in database.items():
        plugin = loaded.get(name)
        description = getattr(plugin, '__description__', None) if plugin else None
        if not isinstance(description, str):
            try:
                with open(filename, 'r', encoding='utf-8') as source:
                    tree = ast.parse(source.read(), filename=filename)
                for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
                    for node in class_node.body:
                        if isinstance(node, ast.Assign) and any(
                                isinstance(target, ast.Name) and target.id == '__description__'
                                for target in node.targets):
                            value = ast.literal_eval(node.value)
                            if isinstance(value, str):
                                description = value
                            break
                    if isinstance(description, str):
                        break
            except (OSError, SyntaxError, ValueError):
                logging.debug("Could not read plugin description from %s", filename, exc_info=True)
        if isinstance(description, str):
            descriptions[name] = description
    return descriptions


'''

old_route = "            return render_template('plugins.html', loaded=plugins.loaded, database=plugins.database)"
new_route = (
    "            return render_template('plugins.html', loaded=plugins.loaded, database=plugins.database,\n"
    "                                   descriptions=_plugin_descriptions(plugins.database, plugins.loaded))"
)

if "def _plugin_descriptions(database, loaded):" not in handler:
    if "import logging" not in handler or "\nclass Handler:\n" not in handler:
        raise SystemExit("Refusing to patch handler.py: unrecognized imports or Handler layout.")
    handler = handler.replace("import logging", "import ast\nimport logging", 1)
    handler = handler.replace("\nclass Handler:\n", f"\n{helper}class Handler:\n", 1)

if "descriptions=_plugin_descriptions(plugins.database, plugins.loaded)" not in handler:
    if handler.count(old_route) != 1:
        raise SystemExit("Refusing to patch handler.py: plugin route was not recognized.")
    handler = handler.replace(old_route, new_route, 1)

old_has_info = "{% set has_info = name in loaded and loaded[name].__description__ is defined %}"
new_has_info = "{% set has_info = name in descriptions %}"
old_description = "{{ loaded[name].__description__ }}"
new_description = "{{ descriptions[name] }}"

if new_has_info not in template:
    if template.count(old_has_info) != 1:
        raise SystemExit("Refusing to patch plugins.html: tooltip condition was not recognized.")
    template = template.replace(old_has_info, new_has_info, 1)
if new_description not in template:
    if template.count(old_description) != 1:
        raise SystemExit("Refusing to patch plugins.html: tooltip value was not recognized.")
    template = template.replace(old_description, new_description, 1)

compile(handler, str(handler_path), "exec")

def write_if_changed(path, original, updated):
    if original == updated:
        print(f"[PwnSafe repair] {path.name} is already fixed.")
        return
    backup = path.with_name(f"{path.name}.pwnsafe-{stamp}.bak")
    shutil.copy2(path, backup)
    stat = path.stat()
    temporary = path.with_name(f"{path.name}.pwnsafe.tmp")
    temporary.write_text(updated, encoding="utf-8")
    os.chmod(temporary, stat.st_mode)
    os.chown(temporary, stat.st_uid, stat.st_gid)
    os.replace(temporary, path)
    print(f"[PwnSafe repair] Fixed {path.name}; backup: {backup}")

write_if_changed(handler_path, original_handler, handler)
write_if_changed(template_path, original_template, template)
PY

"$python_bin" -m py_compile "$handler"
if [[ -f "$enable_assoc" ]]; then
    "$python_bin" -m py_compile "$enable_assoc"
fi

test_plugin="$package_root/plugins/default/auto_backup.py"
if [[ -f "$test_plugin" ]]; then
    "$python_bin" - "$handler" "$test_plugin" <<'PY'
import importlib.util
import pathlib
import sys

handler_path, plugin_path = sys.argv[1:]
spec = importlib.util.spec_from_file_location("pwnsafe_handler_check", handler_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
name = pathlib.Path(plugin_path).stem
descriptions = module._plugin_descriptions({name: plugin_path}, {})
assert descriptions.get(name), "Disabled-plugin description extraction failed"
print("[PwnSafe repair] Disabled-plugin description extraction passed.")
PY
fi

if (( restart_service )); then
    log "Restarting pwnagotchi.service."
    systemctl restart pwnagotchi
    stable=0
    last_pid=
    for _ in $(seq 1 12); do
        state=$(systemctl is-active pwnagotchi 2>/dev/null || true)
        pid=$(systemctl show pwnagotchi -p MainPID --value)
        if [[ "$state" == active && "$pid" != 0 && "$pid" == "$last_pid" ]]; then
            stable=$((stable + 1))
        elif [[ "$state" == active && "$pid" != 0 ]]; then
            stable=1
        else
            stable=0
        fi
        last_pid=$pid
        (( stable >= 6 )) && break
        sleep 5
    done
    if (( stable < 6 )); then
        systemctl status pwnagotchi --no-pager -l || true
        echo "pwnagotchi.service did not remain stable after the repairs." >&2
        exit 1
    fi
    log "pwnagotchi.service is stable (PID $last_pid)."
else
    log "Repairs validated; service restart skipped."
fi

log "All applicable repairs completed."
