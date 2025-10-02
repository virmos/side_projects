from __future__ import annotations
import math
import loguru
import asyncio

from pathlib import Path
from typing import Mapping, Protocol, List
from typing import Dict, List, Mapping
from dataclasses import dataclass
from typing import Protocol
from models.db.price_trie import TriePriceDB
from models.schemas.pricing import PriceEntry
from services.types import IPriceListLoader


class TextPriceListLoader(IPriceListLoader):
    def __init__(self, batch_size: int, db: TriePriceDB):
        self.db = db
        self.batch_size = batch_size
        self.current_operator: str | None = None
        self.line_counter = 0

    async def load_from_file_fast(
        self, path: str, encoding: str = "utf-8"
    ) -> Mapping[str, List[PriceEntry]]:
        base_dir = Path.cwd()
        full_path = base_dir / path
        f = full_path.open("r", encoding=encoding)
        lines = f.read().splitlines()

        total_lines = len(lines)
        num_batch = total_lines // self.batch_size + 1

        for i in range(num_batch):
            batch = lines[self.line_counter : self.line_counter + self.batch_size]
            loguru.logger.info(f"Load batch {i + 1}... in total {num_batch}")
            data = await self._load_batch(batch)
            await self.db.build_data_structure(data)
            self.line_counter += self.batch_size

    async def load_from_file(
        self, path: str, encoding: str = "utf-8"
    ) -> Mapping[str, List[PriceEntry]]:
        base_dir = Path.cwd()
        full_path = base_dir / path
        batch: List[str] = []
        num_batch = 0
        with full_path.open("r", encoding=encoding) as f:
            async for line in self._aiter_file(f):
                batch.append(line.rstrip("\n"))

                if len(batch) >= self.batch_size:
                    num_batch += 1
                    await self.load_batch(batch, num_batch)
                    batch.clear()
            if batch:
                num_batch += 1
                await self.load_batch(batch, num_batch)
                batch.clear()

    async def _aiter_file(self, f):
        loop = asyncio.get_event_loop()
        for line in f:
            yield await loop.run_in_executor(None, lambda l=line: l)

    async def load_batch(self, batch: List[str], num_batch: int) -> None:
        loguru.logger.info(f"Load batch {num_batch}")
        data: Dict[str, List[PriceEntry]] = await self._load_batch(batch)
        await self.db.build_data_structure(data)

    async def _load_batch(self, lines: List[str]) -> Mapping[str, List[PriceEntry]]:
        operator_to_entries: Dict[str, List[PriceEntry]] = {}

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            if line.endswith(":"):
                self.current_operator = line[:-1].strip()
                continue

            if self.current_operator is None:
                continue

            parts = [p for p in line.replace("\t", " ").split(" ") if p]
            if len(parts) != 2:
                continue
            prefix, price_str = parts
            if not prefix.isdigit():
                loguru.logger.info(
                    "Prefix of operator %s is not a string %s".format(
                        self.current_operator, prefix
                    )
                )
                continue
            try:
                price = float(price_str)
            except ValueError:
                loguru.logger.info(
                    "Price of operator %s is not a float %s".format(
                        self.current_operator, prefix
                    )
                )
                continue

            if self.current_operator not in operator_to_entries:
                operator_to_entries[self.current_operator] = []
            operator_to_entries[self.current_operator].append(
                PriceEntry(prefix=prefix, price=price)
            )

        return operator_to_entries
