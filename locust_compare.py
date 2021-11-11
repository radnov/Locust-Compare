"""
Locust-Compare

This script is used to compare the results of the previous Locust run with the current one.
This can be used in a Jenkins pipeline to determine if you want to pass/fail the build step based on the differences.

Sample usage: CI/CI compare against previous run (make sure you have atleast 1 locust run)
  $ python locust_compare.py prefix_stats_previous.csv prefix_stats.csv --column-name 90% --threshold 1
"""

import pandas as pd
import argparse
import sys


class LocustComparer:

    def __init__(self, previous, current, threshold):
        self._previous = previous
        self._current = current
        self._threshold = threshold

    def compare(self, column_name):
        new_df = pd.read_csv(self._current)
        old_df = pd.read_csv(self._previous)

        merged_df = pd.merge(new_df, old_df, on=['Type', 'Name'], how='outer', suffixes=('_new', '_old'))
        compared_columns = merged_df[['Type', 'Name', f'{column_name}_new', f'{column_name}_old']]
        results = compared_columns[f'{column_name}_new'] / compared_columns[f'{column_name}_old']
        print(f'Comparison:\n {compared_columns}\n\n')

        return results

    def validate(self, results):
        results_output = (
            f'Threshold factor: {self._threshold}\n\n'
            f'Difference factors:\n{results}\n'
        )

        if all(result <= self._threshold for result in results.array):
            print(
                f'Success!\n\n' + results_output
            )
        elif any(result > self._threshold for result in results.array):
            sys.exit(
                f'Some of the requests are above the given threshold factor!\n\n' + results_output
            )
        else:
            sys.exit(
                f'An error occurred!\n\n' + results_output
            )


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

    args = parser.parse_args()

    comparer = LocustComparer(args.previous, args.current, args.threshold)

    comparer.validate(comparer.compare(args.column_name))


if __name__ == '__main__':
    exit(main())
