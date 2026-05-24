from pathlib import Path
import subprocess


INCLUDE_THIS_SCRIPT = False
EXCLUDED_FILES = {"test.py"}


def copy_to_clipboard(text: str) -> None:
    """Копирует переданный текст в буфер обмена Windows."""
    subprocess.run(
        "clip",
        input=text,
        text=True,
        encoding="utf-16le",
        check=True
    )


def read_file_text(file_path: Path) -> str:
    """Читает текст файла, пробуя UTF-8 и CP1251."""
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="cp1251")


def collect_py_files() -> str:
    """Собирает содержимое Python-файлов проекта в одну строку."""
    script_path = Path(__file__).resolve()
    folder = script_path.parent

    parts = []

    for file_path in sorted(folder.glob("*.py")):
        if not INCLUDE_THIS_SCRIPT and file_path.resolve() == script_path:
            continue
        if file_path.name in EXCLUDED_FILES:
            continue

        content = read_file_text(file_path)
        parts.append(f"{file_path.name}\n\n{content}")

    return "\n\n".join(parts)


def main():
    """Копирует собранный текст Python-файлов в буфер обмена."""
    result = collect_py_files()

    if not result:
        print("В папке не найдено .py файлов.")
        return

    copy_to_clipboard(result)
    print("Готово. Все .py файлы скопированы в буфер обмена.")


if __name__ == "__main__":
    main()
