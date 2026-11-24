# Spike: BCB Olinda `Pix_DadosAbertos` v1

Verified against the live service on **2026-11-24** (America/Sao_Paulo). Nothing in this note is inferred from the name of a field. Where a check was not done, it says so.

Base URL:

```text
https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/
```

Metadata: append `$metadata`. Responses below used `Accept: application/json` and `$format=json`.

## What changed the ingestion plan

1. **Working resources are the function imports, not the underscore entity sets.** The service document lists both. `GET /_EstatisticasTransacoesPix?$top=1&$format=json` (and the other `_…` sets) returns HTTP 500 with body `/*{ "codigo" : 500, "mensagem" : "Erro desconhecido" }*/`. `PixUsuariosCadastradosDICT` is a real entity set and does respond. Ingestion calls the function imports.
2. **The path argument is a lower bound, and the name differs by resource.** `TransacoesPixPorMunicipio` takes `DataBase`. The other function imports take `Database`, except `ChavesPix`, which takes `Data`. Without `$filter`, one call mixes months. The client always sends `$filter` for the month it intends to write.
3. **`$skip` is broken today, and `$count` is forbidden.** `$skip` returns the same HTTP 500 envelope on function imports and on `PixUsuariosCadastradosDICT`. No response in this spike included `@odata.nextLink`. `/$count` returns HTTP 403 with a Spring body (`{"status":403,"error":"Forbidden",...}`), not the Olinda envelope. A full month of each core entity fit in one `$top` on the October 2026 extract (see counts below). The client still pages with `$top`/`$skip`, retries the 500, and if `$skip` keeps failing it slices the month instead of writing a short page.
4. **The grain is monthly.** Transaction, municipality, CNAE, and fraud rows are keyed by `AnoMes` (`YYYYMM`). `ChavesPix` and `PixUsuariosCadastradosDICT` use a single date, and the dates checked are the last calendar day of the month (`2026-10-31`, `2026-09-30`, `2020-11-30`, `2024-02-29`). There is no daily series in these resources.
5. **There is no per-bank payment volume.** `EstatisticasTransacoesPix` and `TransacoesPixPorMunicipio` have no ISPB. `ChavesPix` is a stock of keys by ISPB, not a value or a count of payments. `EstatisticasFraudesPix` for `202609` returns **one row** with national MED totals and no municipality or institution column.
6. **The open month is real for municipalities only, among the resources checked on this date.** `TransacoesPixPorMunicipio` for `202611` returned rows. `EstatisticasTransacoesPix` for `202611` returned none. `ChavesPix` for November 2026 returned none. Fraud for `202610` and `202611` returned none; `202609` returned the national row. The watermark treats the current São Paulo calendar month as partial for every entity: it may be written, and it is not checkpointed.
7. **On-us exclusion is not visible in the payload.** There is no on-us flag or column. This spike does not treat "on-us transactions are excluded" as something the API response demonstrates. The loader does not filter or label on-us.
8. **Classifications stay raw.** The full `202610` transaction extract (13,373 rows, no nulls) contains nine `NATUREZA` codes. `FORMAINICIACAO` includes codes and the literal string `Nao disponivel`. The contract stores those strings. It does not attach a display name.

Error handling follows the body we got back: HTTP 500 (and 429/502/503/504) is retried with backoff after parsing the `/*{...}*/` envelope. HTTP 400 is not retried. A month that returned data took from about 3 seconds (municipality, keys) to 28 seconds (a full transaction month). The client read timeout is 120 seconds.

A row that fails the Pydantic contract fails that entity, and the raw response is written to `s3://<bucket>/quarantine/<entity>/ano_mes=YYYYMM/` instead of `raw/`.

## Resources

| Service name | Kind | Path parameter | Period field | Used in v0.1 |
| --- | --- | --- | --- | --- |
| `EstatisticasTransacoesPix` | FunctionImport | `Database` (Edm.String, required) | `AnoMes` Edm.Int32 | yes |
| `TransacoesPixPorMunicipio` | FunctionImport | `DataBase` (capital B) | `AnoMes` Edm.Int32 | yes |
| `ChavesPix` | FunctionImport | `Data` (Edm.String, required) | `Data` Edm.Date | yes |
| `CnaePorteRecebedor` | FunctionImport | `Database` | `AnoMes` Edm.Int32 | documented only |
| `EstatisticasFraudesPix` | FunctionImport | `Database` | `AnoMes` Edm.Int32 | documented only |
| `PixUsuariosCadastradosDICT` | EntitySet | none | `DataGraficosPix` Edm.Date | documented only |

Entity sets also published in the service document, all HTTP 500 when read directly: `_EstatisticasTransacoesPix`, `_TransacoesPixPorMunicipio`, `_ChavesPix`, `_CnaePorteRecebedor`, `_EstatisticasFraudesPix`.

Calling a function with the wrong parameter name is HTTP 400, same envelope. Example message: `The function import 'TransacoesPixPorMunicipio' has no function with parameters '[Database]'.`

## The path argument does not select one month

`Database` / `DataBase` means "AnoMes greater than or equal to this value". `Data` on `ChavesPix` behaves the same way for dates.

Evidence:

| Request | Result |
| --- | --- |
| `EstatisticasTransacoesPix(Database='202609')?$top=30&$select=AnoMes` | 16 rows of `202609` and 14 of `202610` |
| `EstatisticasTransacoesPix(Database='202611')?$filter=AnoMes eq 202610&$top=2` | 0 rows |
| `EstatisticasTransacoesPix(Database='202609')?$filter=AnoMes eq 202610&$top=2` | rows of `202610` |
| `TransacoesPixPorMunicipio(DataBase='202612')?$filter=AnoMes eq 202611` | 0 rows |
| `ChavesPix(Data='2026-10-01')?$top=5&$select=Data` | rows dated `2026-10-31`, not `2026-10-01` |
| `ChavesPix(Data='2026-11-01')` with `Data ge 2026-10-01 and Data lt 2026-11-01` | 0 rows |

The filter that isolates a month:

```text
AnoMes eq 202610
Data ge 2026-10-01 and Data lt 2026-11-01
```

Date literals are unquoted. `Data ge '2026-10-01'` returns HTTP 400: `The types 'Edm.Date' and 'Edm.String' are not compatible.`

Spaces must be `%20`. `AnoMes+eq+202610` returns HTTP 400: `The types 'Edm.Boolean' and 'Edm.Int32' are not compatible.` Both a literal `'` and `%27` were accepted in a `NATUREZA eq 'P2P'` filter and in the path `Database=%27202610%27`.

`TransacoesPixPorMunicipio(Database='202610')` (wrong casing) is the HTTP 400 above. `EstatisticasTransacoesPix(DataBase='202610')` fails the same way.

## Pagination

| Mechanism | Result on 2026-11-24 |
| --- | --- |
| `$top` | Honored. `$top=10000` on municipalities returned 5,572 rows, not 10,000. `$top=80000` on transactions returned 13,373. |
| `$skip` | HTTP 500, with and without `$select`, with and without `$filter`, including on `PixUsuariosCadastradosDICT?$top=1&$skip=5`. |
| `@odata.nextLink` | Absent on every 200 response checked. |
| `$count` | HTTP 403 Access Denied. |

October 2026 sizes, one request each, all rows inside the filtered month:

| Entity | Rows | Nulls |
| --- | --- | --- |
| `EstatisticasTransacoesPix` `202610` | 13,373 | none |
| `TransacoesPixPorMunicipio` `202610` | 5,572 | not fully scanned before the load. The `202609` load (5,572 rows) has one null group: `Municipio_Ibge`, `Estado_Ibge`, `Sigla_Regiao` on the `N/D` row |
| `ChavesPix` `2026-10-01` .. `2026-11-01` | 5,971, every `Data` = `2026-10-31` | none |

The default page size is 50,000, above those counts, so a normal month is one request. If a page comes back full and `$skip` still returns 500, transactions are sliced by `NATUREZA` and keys by `TipoChave`, plus a `not (...)` complement so a new code is not dropped. A slice that is itself full fails the entity.

## History and what is published today

Today in this spike is 2026-11-24.

| Resource | Earliest positive check | Latest positive check | Empty checks |
| --- | --- | --- | --- |
| `EstatisticasTransacoesPix` | `202011` has a row | `202610` has 13,373 rows | `202010`, `202611` |
| `TransacoesPixPorMunicipio` | `202011` has a row | `202611` has rows (month still open) | `202612` as a lower bound excludes `202611` |
| `ChavesPix` | `2020-11-30` | `2026-10-31` has 5,971 rows | November 2026 |
| `CnaePorteRecebedor` | `202011` has a row | `202610` has a row | `202611` |
| `EstatisticasFraudesPix` | `202201` has a row | `202609` has 1 row | `202011`, `202109`, `202111`, `202112`, `202610`, `202611` |
| `PixUsuariosCadastradosDICT` | `2020-11-30` | `2026-10-31` | `2026-11-30` |

Fraud is the lagged series. On this date October has been closed for 24 days and is still empty, while September is present. That is consistent with a lag of about a month. The exact lag is not a field. Months between `202011` and `202201` other than the four empty checks above were not scanned, so `202201` is the earliest fraud month **found**, not a proof that no earlier month exists outside that list.

`PixUsuariosCadastradosDICT?$top=2` without `$orderby` is not chronological. One call returned `2025-08-31` and then `2022-01-31`. Do not infer the latest month from the first row. `$filter=DataGraficosPix eq 2026-10-31` is the check that worked. The same unquoted date form works as `Data eq 2026-10-31` on `ChavesPix`.

`ChavesPix(Data='2026-09-01')?$top=3` returned `2026-09-30` first. That alone does not prove mixing, because September has thousands of rows. The October-versus-November pair in the table above is the proof that `Data` is a lower bound.

## `EstatisticasTransacoesPix`

Function: `EstatisticasTransacoesPix(Database='YYYYMM')`.

| Field | Metadata | JSON on 202610 |
| --- | --- | --- |
| `AnoMes` | Edm.Int32 | number |
| `PAG_PFPJ`, `REC_PFPJ` | Edm.String | `PF`, `PJ` |
| `PAG_REGIAO`, `REC_REGIAO` | Edm.String | `CENTRO-OESTE`, `NORDESTE`, `NORTE`, `Nao informado`, `SUDESTE`, `SUL` |
| `PAG_IDADE`, `REC_IDADE` | Edm.String | `Nao informado`, `Nao se aplica`, `até 19 anos`, `entre 20 e 29 anos`, `entre 30 e 39 anos`, `entre 40 e 49 anos`, `entre 50 e 59 anos`, `mais de 60 anos` |
| `FORMAINICIACAO` | Edm.String | `APDN`, `APES`, `AUTO`, `DICT`, `INIC`, `MANU`, `Nao disponivel`, `QRDN`, `QRES` |
| `NATUREZA` | Edm.String | `B2B`, `B2G`, `B2P`, `G2B`, `G2G`, `G2P`, `P2B`, `P2G`, `P2P` |
| `FINALIDADE` | Edm.String | `Nao disponivel`, `Pix`, `Pix Saque`, `Pix Troco` |
| `VALOR`, `QUANTIDADE` | Edm.Decimal | JSON numbers. `VALOR` example `686701.07`. `QUANTIDADE` example `777` (no fractional part in that row). |

`NATUREZA` in the full month is those nine codes and no others. `FORMAINICIACAO` is stored as returned. `Nao disponivel` is the API's own value, not a label added here. This repository does not map `APDN`, `APES`, or the other codes to a Portuguese name.

Sample row (trimmed):

```json
{
  "AnoMes": 202610,
  "PAG_PFPJ": "PJ",
  "REC_PFPJ": "PF",
  "PAG_REGIAO": "NORDESTE",
  "REC_REGIAO": "SUL",
  "PAG_IDADE": "Nao se aplica",
  "REC_IDADE": "mais de 60 anos",
  "FORMAINICIACAO": "Nao disponivel",
  "NATUREZA": "B2P",
  "FINALIDADE": "Nao disponivel",
  "VALOR": 686701.07,
  "QUANTIDADE": 777
}
```

Partition column is `AnoMes`. The client rejects a page that contains any other `AnoMes`.

## `TransacoesPixPorMunicipio`

Function: `TransacoesPixPorMunicipio(DataBase='YYYYMM')`. Note the capital B.

| Field | Metadata | JSON on 202610 |
| --- | --- | --- |
| `AnoMes` | Edm.Int32 | number |
| `Municipio_Ibge`, `Estado_Ibge` | Edm.Int32 | number. Example municipality `2103406`, state `21` |
| `Municipio`, `Estado`, `Sigla_Regiao`, `Regiao` | Edm.String | example `COELHO NETO`, `MARANHÃO`, `NE`, `NORDESTE` |
| `VL_PagadorPF`, `VL_PagadorPJ`, `VL_RecebedorPF`, `VL_RecebedorPJ` | Edm.Decimal | JSON numbers, two decimal places in the sample (`142493207.35`) |
| `QT_PagadorPF`, `QT_PagadorPJ`, `QT_RecebedorPF`, `QT_RecebedorPJ`, `QT_PES_PagadorPF`, `QT_PES_PagadorPJ`, `QT_PES_RecebedorPF`, `QT_PES_RecebedorPJ` | Edm.Decimal | JSON integers in the sample (`1404865`). The contract accepts a decimal because that is the metadata type. |

`202611` is already present (`Municipio` example `CACHOEIRA DO PIRIÁ`) while the month is open. The loader writes it and leaves the watermark on the previous closed month.

The `202609` extract (5,572 rows) has a single row with nulls: `Municipio` `N/D`, `Estado` `NAO INFORMADO`, `Regiao` `Nao informado`, and null `Municipio_Ibge`, `Estado_Ibge`, and `Sigla_Regiao`. Those three codes are optional in the contract. The text values stay as sent. Every other column in that extract was present and non-null. The October null scan was not repeated before the first load; the same shape is what the contract now allows.

## `ChavesPix`

Function: `ChavesPix(Data='YYYY-MM-01')` plus the date-range filter. The path value is the first day of the month so the lower bound includes the snapshot, whatever day it falls on. The partition key is `ano_mes` derived from `Data`, and the `Data` column is kept.

| Field | Metadata | JSON |
| --- | --- | --- |
| `Data` | Edm.Date | string `YYYY-MM-DD`. October 2026 is entirely `2026-10-31`. February 2024 is `2024-02-29`. |
| `ISPB` | Edm.String | string, including leading zeros (`05938780`). Not an integer. |
| `Nome` | Edm.String | institution name, example `COOPER CARD IP` |
| `NaturezaUsuario` | Edm.String | `PF`, `PJ` |
| `TipoChave` | Edm.String | `Aleatória`, `CNPJ`, `CPF`, `Celular`, `e-mail` |
| `qtdChaves` | Edm.Int32 | number |
| `Segmento` | Edm.String | institution segment as sent, for example `Instituição de Pagamento`, `Banco Múltiplo`, `Cooperativa de Crédito` |

October 2026 has 854 distinct `ISPB` values in the 5,971 rows. No nulls and no empty strings in that extract.

## Series that v0.1 does not load

### `EstatisticasFraudesPix`

`EstatisticasFraudesPix(Database='YYYYMM')`. One row per month in the `202609` check (`$top=5` returned a single row). Fields from `$metadata`, all Edm.Decimal except `AnoMes` (Edm.Int32):

`QtdePixcontestados`, `Qtdecontestacoesaceitas`, `Qtdecontestacoesrejeitadas`, `Qtdecontestacoesaceitasacada100mil`, `QtdeUsuarioscommarcacoesdefraude`, `QtdeChavesPixcommarcacoesdefraude`, `ValorPixcontestadosaceitos`, `QuantidadedevolvidaintegralmentepormeiodoMED`, `ValorPixdevolvidosintegralmente`, `QuantidadedevolvidaparcialmentepormeiodoMED`, `ValorPixdevolvidosparcialmente`, `ValorPixresidualnaodevolvido`, `Quantidadedenaodevolvidossaldoinsuficiente`, `ValorPixnaodevolvidossaldoinsuficiente`, `Quantidadedenaodevolvidoscontaencerrada`, `Valornaodevolvidoscontaencerrada`, `Quantidadedenaodevolvidosmotivosdiversos`, `ValorPixnaodevolvidosmotivosdiversos`, `PercentualdeDevolucao`, `QtdePixbloqueadoscautelarmenteeliberados`, `ValorPixbloqueadoscautelarmenteeliberados`, `QtdePixbloqueadoscautelarmenteedevolvidos`, `ValorPixbloqueadoscautelarmenteedevolvidos`.

The `202609` row includes `QtdePixcontestados` 3747045 and `Qtdecontestacoesaceitasacada100mil` 3.834. There is no dimension column. That is the sense in which fraud (MED) is a national total.

### `CnaePorteRecebedor`

`CnaePorteRecebedor(Database='YYYYMM')`. Fields: `AnoMes`, `tipopessoa`, `formainic`, `finalidade`, `porte`, `mei`, `cnssecao`, `mesmatit`, `naturezarel`, `qtpagador`, `qtrecebedor`, `qtlanliq`, `vllanliq`, `vlcompra`, `vldinespec`.

Two live rows, raw values only:

- `202011`: `tipopessoa=PJ`, `formainic=N/D`, `finalidade=NA`, `porte=Microempresa`, `mei=N`, `naturezarel=P2B`
- `202610`: `formainic=DICT`, `finalidade=Pix`, `mei=S`, `naturezarel=B2B`, `cnssecao` starting `R - Artes, cultura, esporte e recreacao`

`formainic` is not the same vocabulary as `FORMAINICIACAO` on the transaction resource (`N/D` versus `Nao disponivel`). Both are stored as sent when that series is loaded later.

### `PixUsuariosCadastradosDICT`

Entity set, no function import. Fields: `DataGraficosPix` (Edm.Date), `qtdUsuariosPessoaFisica`, `qtdUsuariosPessoaJuridica`, `qtdUsuariosCadastradosDICTTotal` (Edm.Int32). Example `2026-10-31`: 168816010, 18969680, 187785690. `2020-11-30` is present. `2026-11-30` is empty. Filter with an unquoted date.

## Ingest run on 2026-11-24

`make ingest` (lookback 3, São Paulo month 202611) against the live API and LocalStack. Exit 0 on the second run, after the municipality contract learned the null codes above. Watermark for every entity is `202610`. `202611` is partial: municipality rows were written, and the checkpoint did not move onto that month.

| Entity | 202609 | 202610 | 202611 | Rows written | Watermark |
| --- | --- | --- | --- | --- | --- |
| `EstatisticasTransacoesPix` | 13,350 | 13,373 | 0 (not written) | 26,723 | 202610 |
| `TransacoesPixPorMunicipio` | 5,572 | 5,572 | 5,572 | 16,716 | 202610 |
| `ChavesPix` | 6,061 | 5,971 | 0 (not written) | 12,032 | 202610 |

A first pass quarantined `TransacoesPixPorMunicipio` `202609` because row 2366 has null IBGE and region codes. That is the `N/D` bucket, not a corrupt page. The contract now allows those three nulls, and the rerun wrote the partition.

## Contract notes for the loader

- Money and quantities use `Decimal`. JSON numbers are parsed with `parse_float=Decimal` so a value such as `142493207.35` is not a binary float.
- `extra` fields are rejected. A new column from Olinda fails the entity and is quarantined instead of being dropped.
- Required fields are those listed above. A null fails the contract. The full transaction month and the full October key extract had no nulls. The municipality null scan was only the rows used to read types, not all 5,572.
- String codes are not enums. A tenth `NATUREZA` would pass the contract and would be picked up by the `not (...)` slice if pagination has to split.
