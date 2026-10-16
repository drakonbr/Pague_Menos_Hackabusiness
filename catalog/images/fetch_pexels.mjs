#!/usr/bin/env node
// Baixa fotos REAIS e SEM MARCA de embalagens de cosméticos no Pexels, por formato de embalagem.
// Roda no seu computador (o ambiente de nuvem não alcança o Pexels).
//
// Uso (PowerShell, na raiz do repositório):
//   $env:PEXELS_API_KEY = "sua-chave"      # chave gratuita em https://www.pexels.com/api/
//   node catalog/images/fetch_pexels.mjs
//
// Saída:
//   catalog/images/raw/<grupo>/pexels-<id>.jpg   candidatas (ainda não revisadas)
//   catalog/images/candidates.json               manifesto: fonte, fotógrafo, licença, data
//
// É seguro rodar de novo: o que já foi baixado é pulado.
// Licença Pexels: uso livre, atribuição não obrigatória; as diretrizes da API pedem link
// visível para o Pexels e crédito ao fotógrafo quando possível (o app mostra os créditos).

import { mkdir, readFile, writeFile, access } from "node:fs/promises";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const RAW = join(HERE, "raw");
const MANIFEST = join(HERE, "candidates.json");
const API = (process.env.PEXELS_API_BASE ?? "https://api.pexels.com/v1").replace(/\/$/, "");
const KEY = process.env.PEXELS_API_KEY;
const PER_GROUP = Number(process.env.PER_GROUP ?? 14);
const PAUSE_MS = Number(process.env.PAUSE_MS ?? 400);

// Grupos = formatos de embalagem do catálogo (campo `form`) + banners da tela inicial.
// Buscas em inglês trazem mais resultados de embalagem lisa ("blank", "mockup", "unbranded").
const GROUPS = {
  tube: { orientation: "square", queries: ["blank cosmetic tube", "white skincare tube mockup", "unbranded cream tube"] },
  bottle: { orientation: "square", queries: ["blank cosmetic bottle", "toner bottle unbranded", "white skincare bottle"] },
  pump: { orientation: "square", queries: ["pump bottle skincare blank", "lotion pump bottle white", "cleanser pump bottle"] },
  jar: { orientation: "square", queries: ["cream jar blank", "white cosmetic jar", "moisturizer jar unbranded"] },
  dropper: { orientation: "square", queries: ["serum dropper bottle", "glass dropper bottle skincare", "facial serum bottle blank"] },
  stick: { orientation: "square", queries: ["sunscreen stick", "balm stick blank", "lip balm stick unbranded"] },
  patch: { orientation: "square", queries: ["pimple patches", "acne patch", "hydrocolloid patch"] },
  spray: { orientation: "square", queries: ["spray bottle cosmetic blank", "facial mist bottle", "sunscreen spray bottle"] },
  bar: { orientation: "square", queries: ["facial soap bar", "white soap bar", "handmade soap bar plain"] },
  banner: { orientation: "landscape", queries: ["skincare products flat lay", "sunscreen summer skin", "skincare routine bathroom"] },
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const exists = (p) => access(p).then(() => true, () => false);

async function search(query, orientation, page = 1) {
  const url = new URL(`${API}/search`);
  url.searchParams.set("query", query);
  url.searchParams.set("orientation", orientation);
  url.searchParams.set("per_page", "30");
  url.searchParams.set("page", String(page));
  const res = await fetch(url, { headers: { Authorization: KEY } });
  if (res.status === 429) throw new Error("Limite de requisições do Pexels atingido (429). Espere 1 hora e rode de novo.");
  if (res.status === 401 || res.status === 403) throw new Error(`Chave recusada pelo Pexels (${res.status}). Confira PEXELS_API_KEY.`);
  if (!res.ok) {
    const e = new Error(`busca "${query}" falhou com ${res.status}`);
    e.recoverable = true;
    throw e;
  }
  return res.json();
}

function sizedUrl(photo, banner) {
  // Pexels aceita parâmetros de redimensionamento na URL original.
  try {
    const u = new URL(photo.src.original);
    u.searchParams.set("auto", "compress");
    u.searchParams.set("cs", "tinysrgb");
    u.searchParams.set("fit", "crop");
    u.searchParams.set("w", banner ? "1200" : "800");
    u.searchParams.set("h", banner ? "600" : "800");
    return u.toString();
  } catch {
    return photo.src.large;
  }
}

async function download(url, file) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`download ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  if (buf.length < 1000) throw new Error("arquivo pequeno demais");
  await mkdir(dirname(file), { recursive: true });
  await writeFile(file, buf);
  return buf.length;
}

async function main() {
  if (!KEY) {
    console.error('Defina a chave antes:  $env:PEXELS_API_KEY = "sua-chave"   (PowerShell)');
    process.exit(1);
  }
  const only = process.argv.slice(2);
  const manifest = (await exists(MANIFEST)) ? JSON.parse(await readFile(MANIFEST, "utf8")) : { source: "Pexels", images: [] };
  const known = new Set(manifest.images.map((i) => i.id));
  const failures = [];

  for (const [group, cfg] of Object.entries(GROUPS)) {
    if (only.length && !only.includes(group)) continue;
    let have = manifest.images.filter((i) => i.group === group).length;
    console.log(`\n[${group}] já tem ${have}; meta ${PER_GROUP}`);
    for (const query of cfg.queries) {
      if (have >= PER_GROUP) break;
      let data;
      try {
        data = await search(query, cfg.orientation);
      } catch (e) {
        if (!e.recoverable) throw e;
        failures.push(e.message);
        continue;
      } finally {
        await sleep(PAUSE_MS);
      }
      for (const photo of data.photos ?? []) {
        if (have >= PER_GROUP) break;
        const id = `pexels-${photo.id}`;
        if (known.has(id)) continue;
        const file = join(RAW, group, `${id}.jpg`);
        try {
          const bytes = await download(sizedUrl(photo, group === "banner"), file);
          manifest.images.push({
            id,
            group,
            file: relative(HERE, file).split("\\").join("/"),
            bytes,
            query,
            alt: photo.alt ?? "",
            avgColor: photo.avg_color ?? null,
            pageUrl: photo.url,
            photographer: photo.photographer,
            photographerUrl: photo.photographer_url,
            license: "Pexels License",
            licenseUrl: "https://www.pexels.com/license/",
            downloadedAt: new Date().toISOString(),
            review: "pendente",
          });
          known.add(id);
          have++;
          process.stdout.write(".");
        } catch (e) {
          failures.push(`${id}: ${e.message}`);
        }
        await sleep(PAUSE_MS / 4);
      }
    }
    // grava a cada grupo, para não perder progresso
    manifest.images.sort((a, b) => a.group.localeCompare(b.group) || a.id.localeCompare(b.id));
    await writeFile(MANIFEST, JSON.stringify(manifest, null, 2) + "\n");
  }

  const byGroup = {};
  for (const i of manifest.images) byGroup[i.group] = (byGroup[i.group] ?? 0) + 1;
  console.log("\n\nResumo por grupo:", byGroup);
  console.log(`Total: ${manifest.images.length} imagens em ${relative(process.cwd(), RAW) || RAW}`);
  if (failures.length) console.log(`Falhas (${failures.length}):\n  ${failures.join("\n  ")}`);
  console.log("\nPróximo passo: revisar as candidatas (marcas legíveis saem). Avise no chat que terminou.");
}

main().catch((e) => {
  console.error(`\nErro: ${e.message}`);
  process.exit(1);
});
