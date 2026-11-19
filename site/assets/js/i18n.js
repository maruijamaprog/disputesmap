// Строки интерфейса: i18n/ru.json, i18n/en.json. Язык: URL (#lang=), затем navigator.language, по умолчанию ru.
import { withV } from './version.js';

let dict = {};
let lang = 'ru';

export function getLang() { return lang; }

export async function setLang(l) {
  lang = l === 'en' ? 'en' : 'ru';
  const res = await fetch(withV(`i18n/${lang}.json`));
  dict = await res.json();
  document.documentElement.lang = lang;
  apply(document);
  return lang;
}

export function detectLang(fromHash) {
  if (fromHash === 'ru' || fromHash === 'en') return fromHash;
  const nav = (navigator.language || 'ru').toLowerCase();
  return nav.startsWith('ru') ? 'ru' : (nav.startsWith('en') ? 'en' : 'ru');
}

/** t('key', {n: 3}) — подстановка {n}. */
export function t(key, params) {
  let s = dict[key] ?? key;
  if (params) for (const [k, v] of Object.entries(params)) s = s.replaceAll(`{${k}}`, v);
  return s;
}

/** Текст из двуязычного поля данных {ru, en}. */
export function tx(obj) {
  if (!obj) return '';
  return obj[lang] || obj.ru || obj.en || '';
}

// Если строки нет в словаре (например, браузер взял старый файл из кэша), остаётся текст из разметки, а не ключ.
export function apply(root) {
  root.querySelectorAll('[data-i18n]').forEach((el) => { const k = el.dataset.i18n; if (k in dict) el.textContent = dict[k]; });
  root.querySelectorAll('[data-i18n-attr]').forEach((el) => {
    // формат: "aria-label:key;title:key2"
    el.dataset.i18nAttr.split(';').forEach((pair) => {
      const [attr, key] = pair.split(':');
      if (attr && key && key.trim() in dict) el.setAttribute(attr.trim(), dict[key.trim()]);
    });
  });
}
