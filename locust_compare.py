"""
Locust-Compare

This script is used to compare the results of a previous/baseline Locust run with the current one.
This can be used in a Jenkins pipeline to determine if you want to pass/fail the build step based on the differences.

Compare single column between two report files, based on a given threshold:
  $ python locust_compare.py prefix_stats_previous.csv prefix_stats.csv --column-name 90% --threshold 1

Compare multiple columns between two report files, based on a given threshold:
  $ python locust_compare.py prefix_stats_previous.csv prefix_stats.csv --column-name 'Average Response Time;90%' --threshold 1
"""
import pandas as pd
import argparse
import sys
from jinja2 import Environment, FileSystemLoader


class LocustComparer:

    def __init__(self, previous, current, threshold):
        self._previous = previous
        self._current = current
        self._threshold = threshold
        self._comparison_tables = []

    def compare(self, column_name):
        new_df = pd.read_csv(self._current)
        old_df = pd.read_csv(self._previous)

        merged_df = pd.merge(new_df, old_df, on=['Type', 'Name'], how='outer', suffixes=('_new', '_old'))
        compared_columns = merged_df[['Type', 'Name', f'{column_name}_new', f'{column_name}_old']]
        results = compared_columns[f'{column_name}_new'] / compared_columns[f'{column_name}_old']

        compared_columns.insert(len(compared_columns.columns), 'Results', results)
        self._comparison_tables.append(dict(title=column_name, body=compared_columns.to_html()))

        print(f'Comparison for {column_name} column:\n {compared_columns.to_string()}\n\n')

        return results.add_prefix(f'({column_name})_')

    def render_report(self, output_file):
        template = Environment(loader=FileSystemLoader('.')).get_template("comparison-template.html")
        html = template.render(tables=self._comparison_tables)
        html_file = open(output_file, "w")
        html_file.write(html)
        html_file.close()

    def validate(self, results):
        print(f'Threshold factor: {self._threshold}\n')

        if all(result <= self._threshold for result in results.array):
            sys.exit()
        elif any(result > self._threshold for result in results.array):
            sys.exit('Some of the requests are above the given threshold factor!')
        else:
            sys.exit('An error occurred!')


def main():
    parser = argparse.ArgumentParser(
        description='Compare previous Locust run csv report with the current one.'
    )

    parser.add_argument(
        'previous',
        help='Previous csv report file to compare to.'
    )

    parser.add_argument(
        'current',
        help='Current csv report file to compare with.'
    )

    parser.add_argument(
        '-c', '--column-name',
        required=True,
        type=str,
        help='Name of column to use for comparison.'
    )

    parser.add_argument(
        '-t', '--threshold',
        required=False,
        type=float,
        default=1.0,
        help='The allowed threshold factor of difference (default: %(default)s).'
    )

    parser.add_argument(
        '-o', '--output',
        required=False,
        type=str,
        default='comparison-report.html',
        help='HTML report file name (default: %(default)s).'
    )

    args = parser.parse_args()

    comparer = LocustComparer(args.previous, args.current, args.threshold)
    results = pd.Series([], dtype=float)

    for column in args.column_name.split(';'):
        results = results.append(comparer.compare(column))

    comparer.render_report(args.output)

    comparer.validate(results)


if __name__ == '__main__':
    exit(main())
