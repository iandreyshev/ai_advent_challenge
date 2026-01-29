"""Запуск приложений с интеллектуальным поиском."""

import os
import platform
import subprocess
from pathlib import Path
from typing import List, Optional, Callable


class AppLauncher:
    """Менеджер запуска приложений с поиском по установленным."""

    def __init__(self, llm_matcher: Optional[Callable[[str, List[str]], str]] = None):
        """
        Args:
            llm_matcher: Функция для умного поиска приложения через LLM.
                         Принимает (запрос, список_приложений) -> имя_приложения
        """
        self.system = platform.system()
        self.llm_matcher = llm_matcher
        self._apps_cache: Optional[List[str]] = None

    def get_installed_apps(self, force_refresh: bool = False) -> List[str]:
        """Возвращает список установленных приложений."""
        if self._apps_cache is not None and not force_refresh:
            return self._apps_cache

        apps = []

        if self.system == "Darwin":  # macOS
            apps = self._get_macos_apps()
        elif self.system == "Windows":
            apps = self._get_windows_apps()
        elif self.system == "Linux":
            apps = self._get_linux_apps()

        self._apps_cache = sorted(set(apps))
        return self._apps_cache

    def _get_macos_apps(self) -> List[str]:
        """Получает список приложений на macOS."""
        apps = []
        app_dirs = [
            Path("/Applications"),
            Path("/System/Applications"),
            Path.home() / "Applications",
        ]

        for app_dir in app_dirs:
            if app_dir.exists():
                for item in app_dir.iterdir():
                    if item.suffix == ".app":
                        apps.append(item.stem)
                    # Проверяем вложенные папки (например, Utilities)
                    if item.is_dir() and not item.suffix:
                        for sub_item in item.iterdir():
                            if sub_item.suffix == ".app":
                                apps.append(sub_item.stem)

        return apps

    def _get_windows_apps(self) -> List[str]:
        """Получает список приложений на Windows."""
        apps = []

        # Стандартные папки с программами
        program_dirs = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
            Path.home() / "AppData" / "Local",
        ]

        # Start Menu shortcuts
        start_menu_dirs = [
            Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        ]

        for menu_dir in start_menu_dirs:
            if menu_dir.exists():
                for item in menu_dir.rglob("*.lnk"):
                    apps.append(item.stem)

        return apps

    def _get_linux_apps(self) -> List[str]:
        """Получает список приложений на Linux."""
        apps = []

        # .desktop файлы
        desktop_dirs = [
            Path("/usr/share/applications"),
            Path("/usr/local/share/applications"),
            Path.home() / ".local" / "share" / "applications",
        ]

        for desktop_dir in desktop_dirs:
            if desktop_dir.exists():
                for item in desktop_dir.glob("*.desktop"):
                    # Читаем Name из .desktop файла
                    try:
                        with open(item, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.startswith("Name="):
                                    apps.append(line.split("=", 1)[1].strip())
                                    break
                    except Exception:
                        apps.append(item.stem)

        return apps

    def find_app(self, query: str) -> Optional[str]:
        """
        Ищет приложение по запросу.
        Сначала точное совпадение, потом частичное, потом через LLM.
        """
        apps = self.get_installed_apps()
        query_lower = query.lower()

        # 1. Точное совпадение (без учёта регистра)
        for app in apps:
            if app.lower() == query_lower:
                return app

        # 2. Частичное совпадение
        matches = [app for app in apps if query_lower in app.lower()]
        if len(matches) == 1:
            return matches[0]

        # 3. Приложение начинается с запроса
        starts_with = [app for app in apps if app.lower().startswith(query_lower)]
        if len(starts_with) == 1:
            return starts_with[0]

        # 4. LLM для умного поиска (если есть несколько кандидатов или нет совпадений)
        if self.llm_matcher:
            candidates = matches or starts_with or apps
            return self.llm_matcher(query, candidates)

        # 5. Возвращаем первое частичное совпадение или None
        return matches[0] if matches else None

    def launch(self, app_name: str) -> tuple[bool, str]:
        """
        Запускает приложение по имени.
        Возвращает (успех, сообщение).
        """
        try:
            if self.system == "Darwin":
                subprocess.Popen(
                    ["open", "-a", app_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif self.system == "Windows":
                # Пытаемся запустить через start
                subprocess.Popen(
                    f'start "" "{app_name}"',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:  # Linux
                # Пытаемся найти команду
                subprocess.Popen(
                    [app_name.lower().replace(" ", "-")],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            return True, f"✅ Запущено: {app_name}"

        except Exception as e:
            return False, f"❌ Не удалось запустить {app_name}: {e}"

    def launch_by_query(self, query: str) -> str:
        """
        Ищет и запускает приложение по запросу.
        Возвращает сообщение о результате.
        """
        app = self.find_app(query)

        if not app:
            # Показываем похожие приложения
            apps = self.get_installed_apps()
            similar = [a for a in apps if query.lower()[:3] in a.lower()][:5]
            msg = f"❌ Приложение '{query}' не найдено."
            if similar:
                msg += f"\n   Похожие: {', '.join(similar)}"
            return msg

        success, message = self.launch(app)
        return message

    def list_apps(self, filter_query: str = "") -> str:
        """Возвращает список приложений (с фильтрацией)."""
        apps = self.get_installed_apps()

        if filter_query:
            apps = [a for a in apps if filter_query.lower() in a.lower()]

        if not apps:
            return "❌ Приложения не найдены."

        # Группируем по первой букве для удобства
        result = [f"📱 Найдено приложений: {len(apps)}\n"]

        # Показываем первые 30 или все если с фильтром
        display_apps = apps if filter_query else apps[:30]
        result.append(", ".join(display_apps))

        if not filter_query and len(apps) > 30:
            result.append(f"\n... и ещё {len(apps) - 30}")
            result.append("\nИспользуйте /apps <фильтр> для поиска")

        return "\n".join(result)


# Глобальный экземпляр для обратной совместимости
_launcher: Optional[AppLauncher] = None


def get_launcher(llm_matcher: Optional[Callable] = None) -> AppLauncher:
    """Получает или создаёт глобальный экземпляр лаунчера."""
    global _launcher
    if _launcher is None:
        _launcher = AppLauncher(llm_matcher)
    elif llm_matcher and _launcher.llm_matcher is None:
        _launcher.llm_matcher = llm_matcher
    return _launcher


def launch_app(query: str, llm_matcher: Optional[Callable] = None) -> str:
    """Ищет и запускает приложение по запросу."""
    launcher = get_launcher(llm_matcher)
    return launcher.launch_by_query(query)


def list_installed_apps(filter_query: str = "") -> str:
    """Возвращает список установленных приложений."""
    launcher = get_launcher()
    return launcher.list_apps(filter_query)


# Обратная совместимость со старой функцией
def launch_workspace_apps() -> str:
    """
    Открывает набор рабочих приложений (для обратной совместимости).
    """
    launcher = get_launcher()
    workspace = ["Google Chrome", "Visual Studio Code", "Terminal"]

    print("🚀 Запуск рабочего окружения...")
    results = []

    for app_query in workspace:
        app = launcher.find_app(app_query)
        if app:
            success, msg = launcher.launch(app)
            results.append(msg)
        else:
            results.append(f"⚠️  {app_query} не найден")

    return "\n".join(results)
