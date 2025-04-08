import sys
import chdb
from mock_api.api import get_data
from chdb.utils import infer_data_types, convert_to_columnar


class DataReader(chdb.PyReader):
    def __init__(self, table_name: str):
        self.table_name = table_name
        raw_data = get_data(table_name)["data"]
        self.data = convert_to_columnar(raw_data)
        self.cursor = 0
        super().__init__(self.data)

    def get_schema(self):
        return infer_data_types(self.data)

    def read(self, col_names, count):
        if not self.data or self.cursor >= len(next(iter(self.data.values()))):
            self.cursor = 0
            return []

        start = self.cursor
        end = min(start + count, len(next(iter(self.data.values()))))
        self.cursor = end

        return [self.data[col][start:end] for col in col_names]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            """
Usage: python data_reader.py TABLE_NAME SQL [outputFormat]
    - TABLE_NAME: Name of the table to query (e.g., 'users', 'comments')
    - SQL: SQL query to run on the data, `FROM Python(reader)` could be omitted. eg:
      - "SELECT * LIMIT 10;"
      - "DESCRIBE Python(reader)"
    - outputFormat: Output format, e.g. Dataframe, CSV, JSON, PrettyCompact
"""
        )
        sys.exit(1)

    table_name = sys.argv[1]
    reader = DataReader(table_name)

    output_format = "PrettyCompact"
    if len(sys.argv) > 2:
        sql = sys.argv[2].strip()
        if len(sys.argv) == 4:
            output_format = sys.argv[3]

        sql_lower = sql.lower()
        if "from" not in sql_lower and sql_lower.startswith("select"):
            sql = "FROM Python(reader) " + sql

        print(chdb.query(sql, output_format))
