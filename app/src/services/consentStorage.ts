// #42: a escolha "serviço de linguagem externo" fica neste aparelho e vale depois de recarregar a página.
const KEY = "pm.useExternalLanguageService";

export function readExternalChoice(): boolean | undefined {
  try {
    const v = localStorage.getItem(KEY);
    return v === "1" ? true : v === "0" ? false : undefined;
  } catch {
    return undefined; // armazenamento bloqueado ou indisponível: vale o padrão da persona
  }
}

export function saveExternalChoice(value: boolean): void {
  try {
    localStorage.setItem(KEY, value ? "1" : "0");
  } catch {
    /* sem armazenamento: a escolha vale só até recarregar */
  }
}
