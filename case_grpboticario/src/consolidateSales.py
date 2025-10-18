from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd

"""
consolidateSales.py

Resumo:
- Procura por arquivos .xlsx/.xls na pasta data_raw (no mesmo nível do projeto).
- Concatena os dados das planilhas encontradas em uma sheet "raw_concatenated".
- Gera 4 visões consolidadas e salva tudo em data_processed/consolidated_sales.xlsx:
    1) Consolidado por ano e mês
    2) Consolidado por marca e linha
    3) Consolidado por marca, ano e mês
    4) Consolidado por linha, ano e mês
"""

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class SalesConsolidator:
    """
    Classe responsável por ler arquivos de vendas brutas, normalizar e gerar
    as visões consolidadas solicitadas.
    """

    RAW_DIR = Path("case_grpboticario/data/data_raw")
    OUT_DIR = Path("case_grpboticario/data/data_processed")
    OUT_FILE = OUT_DIR / "consolidated_sales.xlsx"

    # Possíveis palavras-chave para detecção de colunas
    DATE_KEYS = ("data_venda", "data", "date")
    BRAND_KEYS = ("marca", "brand")
    LINE_KEYS = ("linha", "line", "linha_produto", "product_line", "linha de produto")
    SALES_KEYS = ("qtd_venda", "quantidade", "qty", "quantidade_vendida")

    def __init__(self, raw_dir: Optional[Path] = None, out_dir: Optional[Path] = None) -> None:
        if raw_dir:
            self.RAW_DIR = Path(raw_dir)
        if out_dir:
            self.OUT_DIR = Path(out_dir)
            self.OUT_FILE = self.OUT_DIR / self.OUT_FILE.name

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Cria diretórios necessários se não existirem."""
        if not self.RAW_DIR.exists():
            raise FileNotFoundError(f"Pasta de dados brutos não encontrada: {self.RAW_DIR.resolve()}")
        self.OUT_DIR.mkdir(parents=True, exist_ok=True)

    def discover_files(self) -> List[Path]:
        """Descobre arquivos Excel na pasta data_raw."""
        files = sorted(self.RAW_DIR.glob("*.xlsx")) + sorted(self.RAW_DIR.glob("*.xls"))
        logging.info("Arquivos encontrados em %s: %s", self.RAW_DIR, [f.name for f in files])
        return files

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Padroniza nomes de colunas para lower_snake_case sem acentuação."""
        def slug(col: str) -> str:
            col = str(col).lower().strip()
            col = re.sub(r"[^\w\s]", "", col)
            col = re.sub(r"\s+", "_", col)
            return col

        df = df.rename(columns=lambda c: slug(c))
        return df

    @staticmethod
    def _find_column(columns: List[str], keywords: Tuple[str, ...]) -> Optional[str]:
        """
        Procura por uma coluna que contenha alguma das keywords.
        Retorna o nome da coluna (após normalização) ou None.
        """
        for kw in keywords:
            for col in columns:
                if kw in col:
                    return col
        return None

    @staticmethod
    def _parse_number_series(s: pd.Series) -> pd.Series:
        """
        Tenta converter uma série para float, lidando com formatos comuns
        (p.ex. '1.234,56' ou '1,234.56').
        """
        def to_float(x):
            if pd.isna(x):
                return None
            x_str = str(x).strip()
            # Remove currency symbols and spaces
            x_str = re.sub(r"[^\d,.\-]", "", x_str)
            if x_str == "":
                return None
            # If contains both '.' and ',', decide based on last separator
            if "." in x_str and "," in x_str:
                # assume '.' é milhar e ',' decimal -> 1.234,56
                if x_str.rfind(",") > x_str.rfind("."):
                    x_str = x_str.replace(".", "").replace(",", ".")
                else:
                    x_str = x_str.replace(",", "").replace(".", ".")
            else:
                # If only comma and no dot, comma is decimal
                if "," in x_str and "." not in x_str:
                    x_str = x_str.replace(",", ".")
                # else keep as is
            try:
                return float(x_str)
            except Exception:
                return None

        return s.map(to_float)

    def load_and_concatenate(self, files: List[Path]) -> pd.DataFrame:
        """
        Lê cada arquivo excel (todas as sheets do arquivo serão lidas e concatenadas),
        normaliza colunas e concatena tudo em um único DataFrame.
        """
        frames: List[pd.DataFrame] = []
        for file in files:
            logging.info("Lendo: %s", file.name)
            try:
                # Lê todas as sheets
                xls = pd.read_excel(file, sheet_name=None)
            except Exception as exc:
                logging.warning("Falha ao ler %s: %s", file.name, exc)
                continue

            for sheet_name, df in xls.items():
                if df.empty:
                    continue
                df = self._normalize_columns(df)
                df["_source_file"] = file.name
                df["_source_sheet"] = sheet_name
                frames.append(df)

        if not frames:
            raise ValueError("Nenhum dado foi carregado dos arquivos fornecidos.")
        concatenated = pd.concat(frames, ignore_index=True, sort=False)
        logging.info("Dados concatenados: %d linhas", len(concatenated))
        return concatenated

    def standardize_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identifica colunas essenciais (date, brand, line, sales) e normaliza valores.
        Adiciona colunas auxiliares: year, month (nome), year_month (YYYY-MM).
        """
        cols = list(df.columns)
        date_col = self._find_column(cols, self.DATE_KEYS)
        brand_col = self._find_column(cols, self.BRAND_KEYS)
        line_col = self._find_column(cols, self.LINE_KEYS)
        sales_col = self._find_column(cols, self.SALES_KEYS)

        logging.info("Detecção de colunas -> date: %s, brand: %s, line: %s, sales: %s",
                     date_col, brand_col, line_col, sales_col)

        if not sales_col:
            raise ValueError("Coluna de vendas não encontrada automaticamente. Renomeie sua coluna para algo como 'vendas' ou 'amount'.")

        # Cria cópias padronizadas
        df = df.copy()
        if date_col:
            df["date"] = pd.to_datetime(df[date_col], errors="coerce")
        else:
            # Se não tem data, deixa NaT
            df["date"] = pd.NaT

        df["brand"] = df[brand_col] if brand_col else None
        df["line"] = df[line_col] if line_col else None

        df["sales"] = df[sales_col]

        # Dropar linhas sem quantidade de venda
        before = len(df)
        df = df[df["sales"] > 0].reset_index(drop=True)
        logging.info("Linhas com vendas válidas: %d (removidas %d)", len(df), before - len(df))

        # Preencher vazios de brand/line com 'UNKNOWN' para categorização
        df["brand"] = df["brand"].fillna("UNKNOWN").astype(str).str.strip()
        df["line"] = df["line"].fillna("UNKNOWN").astype(str).str.strip()

        # Year, month, year_month
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["month_name"] = df["date"].dt.strftime("%Y-%m")  # YYYY-MM
        # Para casos sem data, colocar year/month como Unknown
        df["year"] = df["year"].fillna(0).astype(int)
        df["month"] = df["month"].fillna(0).astype(int)
        df["year_month"] = df["date"].dt.strftime("%Y-%m").fillna("unknown")

        # Seleciona e organiza colunas para saída
        cols_out = [
            "_source_file",
            "_source_sheet",
            "date",
            "year",
            "month",
            "year_month",
            "month_name",
            "brand",
            "line",
            "sales_raw",
            "sales",
        ]
        available = [c for c in cols_out if c in df.columns]
        return df[available]

    @staticmethod
    def _aggregate_by(df: pd.DataFrame, group_by: List[str], agg_col: str = "sales") -> pd.DataFrame:
        """Agrupa e soma a coluna de vendas."""
        grouped = df.groupby(group_by, dropna=False, as_index=False)[agg_col].sum()
        # Ordena por todas as colunas de group_by para estabilidade
        grouped = grouped.sort_values(by=group_by).reset_index(drop=True)
        return grouped
    
    def build_views(self, df: pd.DataFrame) -> dict:
        """
        Gera as quatro visões solicitadas e retorna um dicionário nome->DataFrame.
        Views:
            - raw_concatenated: dados padronizados
            - por_ano_mes: Consolidado por ano e mês
            - por_marca_linha: Consolidado por marca e linha
            - por_marca_ano_mes: Consolidado por marca, ano e mês
            - por_linha_ano_mes: Consolidado por linha, ano e mês
        """
        views = {}
        views["raw_concatenated"] = df.copy()

        # a) Consolidado de vendas por ano e mês
        views["por_ano_mes"] = self._aggregate_by(df, ["year", "month", "year_month"])

        # b) Consolidado de vendas por marca e linha
        views["por_marca_linha"] = self._aggregate_by(df, ["brand", "line"])

        # c) Consolidado de vendas por marca, ano e mês
        views["por_marca_ano_mes"] = self._aggregate_by(df, ["brand", "year", "month", "year_month"])

        # d) Consolidado de vendas por linha, ano e mês
        views["por_linha_ano_mes"] = self._aggregate_by(df, ["line", "year", "month", "year_month"])

        logging.info("Visões geradas: %s", list(views.keys()))
        return views

    def save_views_to_excel(self, views: dict) -> None:
        """Salva todas as views em um arquivo Excel com múltiplas sheets."""
        logging.info("Salvando arquivo em %s", self.OUT_FILE)
        with pd.ExcelWriter(self.OUT_FILE, engine="openpyxl", datetime_format="yyyy-mm-dd") as writer:
            for sheet_name, df in views.items():
                # Garantir nomes de sheet compatíveis (<=31 chars)
                safe_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=safe_name, index=False)
        logging.info("Arquivo salvo com sucesso.")

    def run(self) -> None:
        """Fluxo principal: descobrir, carregar, padronizar, agregar e salvar."""
        files = self.discover_files()
        if not files:
            raise FileNotFoundError(f"Nenhum arquivo Excel encontrado em {self.RAW_DIR}")

        raw = self.load_and_concatenate(files)
        standardized = self.standardize_schema(raw)
        views = self.build_views(standardized)
        self.save_views_to_excel(views)


def main():
    """
    Ponto de entrada simples. Ajuste os paths se necessário.
    Executar como: python consolidateSales.py
    """
    try:
        consolidator = SalesConsolidator()
        consolidator.run()
    except Exception as e:
        logging.error("Processo finalizado com erro: %s", e)
        raise


if __name__ == "__main__":
    main()