"""
Split cartera_bonos.parquet (148 MB) into two clean period partitions (<90 MB each):
- cartera_bonos_2016_2020.parquet (2016-11 to 2020-12, ~5.08M rows, ~86 MB)
- cartera_bonos_2021_2024.parquet (2021-01 to 2024-07, ~3.62M rows, ~62 MB)
Ensures 100% compliance with GitHub Pages file size limits (< 100 MB).
"""
import os
import time
import pyarrow.parquet as pq
import pyarrow.compute as pc

def main():
    src_file = "seguros/circular_1835_cartera/outputs/vida/cartera_bonos.parquet"
    out_dir = "seguros/circular_1835_cartera/outputs/vida"
    part1_file = os.path.join(out_dir, "cartera_bonos_2016_2020.parquet")
    part2_file = os.path.join(out_dir, "cartera_bonos_2021_2024.parquet")

    print(f"Abriendo {src_file}...")
    pf = pq.ParquetFile(src_file)
    schema = pf.schema_arrow

    writer1 = pq.ParquetWriter(part1_file, schema, compression="snappy")
    writer2 = pq.ParquetWriter(part2_file, schema, compression="snappy")
    rows1, rows2 = 0, 0
    t0 = time.time()

    try:
        for i in range(pf.num_row_groups):
            rg_table = pf.read_row_group(i)
            mask1 = pc.less_equal(rg_table["periodo"], "2020-12")
            tbl1 = rg_table.filter(mask1)
            if len(tbl1) > 0:
                writer1.write_table(tbl1)
                rows1 += len(tbl1)

            mask2 = pc.greater(rg_table["periodo"], "2020-12")
            tbl2 = rg_table.filter(mask2)
            if len(tbl2) > 0:
                writer2.write_table(tbl2)
                rows2 += len(tbl2)

            if (i + 1) % 5 == 0 or i == pf.num_row_groups - 1:
                print(f"Grupo {i+1}/{pf.num_row_groups}... Part1: {rows1:,} filas, Part2: {rows2:,} filas")
    finally:
        writer1.close()
        writer2.close()

    elapsed = time.time() - t0
    size1 = os.path.getsize(part1_file) / (1024 * 1024)
    size2 = os.path.getsize(part2_file) / (1024 * 1024)
    print(f"\nParticionamiento finalizado en {elapsed:.1f}s:")
    print(f"  Part 1 (2016-2020): {rows1:,} filas, {size1:.2f} MB")
    print(f"  Part 2 (2021-2024): {rows2:,} filas, {size2:.2f} MB")

if __name__ == "__main__":
    main()
