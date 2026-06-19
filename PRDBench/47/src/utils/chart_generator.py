# -*- coding: utf-8 -*-
"""Chart generation utilities — saves PNG files to data/charts/."""

import os
from typing import Optional

from config.settings import FILE_PATHS


class ChartGenerator:
    """Generates statistical charts using Matplotlib."""

    def __init__(self) -> None:
        self.output_dir = FILE_PATHS['charts_dir']
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_bar_chart(
        self,
        data: dict,
        title: str = 'Bar Chart',
        xlabel: str = 'X',
        ylabel: str = 'Y',
        filename: str = 'bar_chart.png',
    ) -> Optional[str]:
        """Generate and save a bar chart.

        Returns:
            Absolute path to the saved PNG file, or None on error.
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            labels = list(data.keys())
            values = list(data.values())

            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(labels, values, color='steelblue', edgecolor='black')
            ax.set_title(title, fontsize=14)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.tick_params(axis='x', rotation=30)

            for bar in bars:
                ax.annotate(
                    str(int(bar.get_height())),
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 3), textcoords='offset points',
                    ha='center', va='bottom',
                )

            plt.tight_layout()
            out_path = os.path.join(self.output_dir, filename)
            plt.savefig(out_path, dpi=100, bbox_inches='tight')
            plt.close(fig)
            return out_path
        except Exception as e:
            print(f"Bar chart generation error: {e}")
            return None

    def generate_pie_chart(
        self,
        data: dict,
        title: str = 'Pie Chart',
        filename: str = 'pie_chart.png',
    ) -> Optional[str]:
        """Generate and save a pie chart.

        Returns:
            Absolute path to the saved PNG file, or None on error.
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            labels = list(data.keys())
            values = list(data.values())

            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(
                values,
                labels=labels,
                autopct='%1.1f%%',
                startangle=140,
                wedgeprops={'edgecolor': 'white'},
            )
            ax.set_title(title, fontsize=14)

            plt.tight_layout()
            out_path = os.path.join(self.output_dir, filename)
            plt.savefig(out_path, dpi=100, bbox_inches='tight')
            plt.close(fig)
            return out_path
        except Exception as e:
            print(f"Pie chart generation error: {e}")
            return None


chart_generator = ChartGenerator()
