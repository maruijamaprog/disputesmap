// Версия сборки из <html data-v="…"> (её ставит scripts/set_version.py).
// Добавляется к адресам файлов данных и строк интерфейса, чтобы после обновления сайта
// браузер и GitHub Pages не отдавали вперемешку старые и новые копии из кэша.
export const VERSION = document.documentElement.dataset.v || '';

export function withV(url) {
  if (!VERSION) return url;
  return `${url}${url.includes('?') ? '&' : '?'}v=${encodeURIComponent(VERSION)}`;
}
