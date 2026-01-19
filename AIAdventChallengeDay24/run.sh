#!/usr/bin/env bash
set -euo pipefail

# =============================
# Config via ENV (required)
# =============================
: "${RC_RELEASE_BOT_ID:?Set RC_RELEASE_BOT_ID (Rocket.Chat bot user id)}"
: "${RC_RELEASE_BOT_AUTH_TOKEN:?Set RC_RELEASE_BOT_AUTH_TOKEN (Rocket.Chat bot token)}"
: "${RC_RECEIVER_ID:?Set RC_RECEIVER_ID (e.g. '#ivan.andreyshev' or roomId)}"

# Optional: default Git remote
GIT_REMOTE="${GIT_REMOTE:-origin}"

# =============================
# Helpers
# =============================
log()   { printf "🤖: %s\n" "$*"; }
fail()  { printf "🤖: ERROR: %s\n" "$*" >&2; exit 1; }

validate_version() {
  local v="$1"
  [[ "$v" =~ ^[0-9]+(\.[0-9]+)*$ ]] || fail "Версия должна содержать только цифры и точки: '$v'"
}

detect_platform_from_market() {
  case "$1" in
    "App Store")   echo "ios" ;;
    "Google Play") echo "android" ;;
    "AppGallery")  echo "android" ;;
    "RuStore")     echo "android" ;;
    *) fail "Неизвестный маркет: '$1'. Ожидается: App Store | Google Play | AppGallery | RuStore" ;;
  esac
}

detect_market_icon_from_market() {
  case "$1" in
    "App Store")   echo ":app_store:" ;;
    "Google Play") echo ":google_play:" ;;
    "AppGallery")  echo ":appgallery:" ;;
    "RuStore")     echo ":rustore:" ;;
    *) fail "Неизвестный маркет: '$1'. Ожидается: App Store | Google Play | AppGallery | RuStore" ;;
  esac
}

# $1 - App
# $2 - Platform
# $3 - Version
detect_tag_prefix_from_app() {
  case "$1" in
    "iSpring Learn") echo "$2-$3" ;;
    "Спринт")        echo "sprint-$2-$3" ;;
    *) fail "Неизвестное название приложения: '$1'. Ожидается: Learn | Sprint" ;;
  esac
}

# $1 - App
detect_app_icon_from_app() {
  case "$1" in
    "iSpring Learn") echo ":ispring_learn_app:" ;;
    "Спринт")        echo ":sprint_app:" ;; 
    *) fail "Неизвестное название приложения: '$1'. Ожидается: Learn | Sprint"     ;;
  esac
}

urlencode_curly_tag() {
  local tag="$1"
  printf "%%7B%s%%7D" "$tag"
}

json_escape() {
  local s="$1"
  s=${s//$'\r'/}
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  s=${s//$'\n'/\\n}
  s=${s//$'\t'/\\t}
  printf "%s" "$s"
}

build_rc_payload() {
  if command -v jq >/dev/null 2>&1; then
    jq -n --arg r "$1" --arg t "$2" \
      '{roomId: $r, text: $t}'
  else
    printf '{"roomId":"%s","text":"%s"}' \
      "$(json_escape "$1")" "$(json_escape "$2")"
  fi
}

post_to_rocketchat() {
  local text="$1"

  local json
  json="$(build_rc_payload "$RC_RECEIVER_ID" "$text")"

  local resp http
  resp=$(curl -v -sS -X POST "https://rocket.cpslabs.net/api/v1/chat.postMessage" \
      -H "Content-Type: application/json" \
      -H "x-User-Id: $RC_RELEASE_BOT_ID" \
      -H "x-Auth-Token: $RC_RELEASE_BOT_AUTH_TOKEN" \
      -d "$json" -w "\n%{http_code}") || fail "Не удалось выполнить запрос к Rocket.Chat"
  http="${resp##*$'\n'}"
  local body="${resp%$'\n'*}"

  [[ "$http" == "200" ]] || fail "Rocket.Chat вернул HTTP $http. Тело: $body"
  echo "$body" | grep -q '"success":true' || fail "Rocket.Chat не подтвердил отправку: $body"
}

merge_release_into_master() {
  local repo_dir="$1"     # /path/to/android_apps or /path/to/mobile_apps
  local rel_branch="$2"   # release_4.3.2

  [[ -d "$repo_dir/.git" ]] || fail "Не найден git-репозиторий: $repo_dir"
  log "Перемещаюсь в директорию '$repo_dir'"
  pushd "$repo_dir" >/dev/null

  log "Fetch из удалённого репозитория ($GIT_REMOTE)…"
  git fetch "$GIT_REMOTE" --prune

  log "Проверка существования ветки '$rel_branch'…"
  if ! git show-ref --verify --quiet "refs/remotes/$GIT_REMOTE/$rel_branch" && \
     ! git show-ref --verify --quiet "refs/heads/$rel_branch"; then
    popd >/dev/null
    fail "Ветка релиза '$rel_branch' не найдена ни локально, ни удалённо."
  fi

  log "Переключение на master и обновление…"
  git checkout master
  git reset --hard "$GIT_REMOTE/master"
  git pull --ff-only "$GIT_REMOTE" master

  # Если релиз уже слит в master — сообщить и не пытаться мержить.
  # Проверим: есть ли локальная ветка?
  if git show-ref --verify --quiet "refs/heads/$rel_branch"; then
    branch_ref="$rel_branch"
  # Если нет — попробуем взять удалённую
  elif git show-ref --verify --quiet "refs/remotes/$GIT_REMOTE/$rel_branch"; then
    branch_ref="$GIT_REMOTE/$rel_branch"
  else
    fail "Ветка релиза '$rel_branch' не найдена ни локально, ни на удалённом."
  fi

  # Теперь проверка "уже подмержена"
  if git diff --quiet "$branch_ref" "$GIT_REMOTE/master"; then
    log "Ветка '$branch_ref' уже подмержена в master. Пропускаю merge."
    MERGE_RESULT="👌 Ветка уже смержена в master"
    popd >/dev/null
    return 0
  fi

  log "Мерж release → master…"
  set +e
  git merge --no-ff --no-edit "$branch_ref"
  local ec=$?
  set -e
  if [[ $ec -ne 0 ]]; then
    log "Конфликт мержа. Откатываю…"
    git merge --abort || true
    popd >/dev/null
    fail "Конфликт при мержe ветки '$branch_ref' в master."
  fi

  log "Пуш в master…"
  git push "$GIT_REMOTE" master
  MERGE_RESULT="🤝 Смержил ветку в master"

  popd >/dev/null
}

# =============================
# CLI parsing
# =============================
usage() {
  cat <<'USAGE'
Usage:
  ./run.sh -v <version> -n "<release-notes>" -m "<market>" [-b "<branch>"] -a "<app-name>"

Required:
  -v  Версия релиза (только цифры и точки), напр. 4.20.0
  -n  Релиз-нотис (произвольный текст, можно с переносами строк)
  -m  Маркет: "App Store" | "Google Play" | "AppGallery" | "RuStore"
  -a  Название приложение: "iSpring Learn" | "Спринт"

Optional:
  -b  Имя ветки, которую нужно смержить. Если не указано — будет использована release_<version>

ENV (обязательные):
  RC_RELEASE_BOT_ID, RC_RELEASE_BOT_AUTH_TOKEN, RC_RECEIVER_ID
Optional ENV:
  GIT_REMOTE (default: origin)

Примеры:
  # Явно указываем ветку
  ./run.sh -v 4.20.0 -m "Google Play" -b "hotfix/login-crash" -n $'Фиксы...' -a "iSpring Learn"

  # Без -b → возьмётся release_4.20.0
  ./run.sh -v 4.20.0 -m "Google Play" -n $'Фиксы...' -a "iSpring Learn"
USAGE
  exit 1
}

VERSION=""
NOTES=""
MARKET=""
BRANCH=""
APP_NAME=""

while getopts ":v:n:m:b:a:" opt; do
  case "$opt" in
    v) VERSION="$OPTARG" ;;
    n) NOTES="$OPTARG" ;;
    m) MARKET="$OPTARG" ;;
    b) BRANCH="$OPTARG" ;;
    a) APP_NAME="$OPTARG" ;;
    *) usage ;;
  esac
done

[[ -z "$VERSION" || -z "$NOTES" || -z "$MARKET" ]] && usage

# =============================
# Derive paths & values
# =============================
validate_version "$VERSION"
PLATFORM="$(detect_platform_from_market "$MARKET")"
APP_ICON="$(detect_app_icon_from_app "$APP_NAME")"
MARKET_ICON="$(detect_market_icon_from_market "$MARKET")"

# если ветка не передана — делаем как раньше: release_<version>
if [[ -z "${BRANCH:-}" || "$BRANCH" == "default" ]]; then
  RELEASE_BRANCH="release_${VERSION}"
else
  RELEASE_BRANCH="$BRANCH"
fi
log "🤖 Релизная ветка для мержа: '$RELEASE_BRANCH'"

# repo roots (assuming sibling folders to tools/)
ROOT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
ANDROID_REPO="$ROOT_DIR/android_apps"
IOS_REPO="$ROOT_DIR/mobile_apps"

# YouTrack link
TAG_PREFIX="$(detect_tag_prefix_from_app "$APP_NAME" "$PLATFORM" "$VERSION")"
ENCODED_TAG="$(urlencode_curly_tag "$TAG_PREFIX")"
YT_LINK="https://youtrack.ispring.lan/issues?q=tag:%20$ENCODED_TAG"

# =============================
# 1) Merge release → master
# =============================
case "$PLATFORM" in
  android)
    log "Платформа ANDROID → мержим в репозиторий: $ANDROID_REPO"
    merge_release_into_master "$ANDROID_REPO" "$RELEASE_BRANCH" || true
    ;;
  ios)
    log "Платформа iOS → мержим в репозиторий: $IOS_REPO"
    merge_release_into_master "$IOS_REPO" "$RELEASE_BRANCH" || true
    ;;
esac

# =============================
# 2) Post message to Rocket.Chat (в любом случае)
# =============================
MESSAGE=$(cat <<TXT
${APP_ICON} ${MARKET_ICON} *${APP_NAME} ${VERSION} опубликован в ${MARKET}*

*Основные изменения:*
${NOTES}

🚀 [Полный список задач](${YT_LINK})
${MERGE_RESULT}
TXT
)

log "Отправляю сообщение в Rocket.Chat…"
post_to_rocketchat "$MESSAGE"
log "Готово ✅"
