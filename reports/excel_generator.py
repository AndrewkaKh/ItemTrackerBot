import pandas as pd
from config import REPORT_FOLDER
import os

def generate_excel(stock_data, movement_data, stock_pay_user_data):
    """
    Генерация Excel отчета.
    :param stock_data: Список остатков на складе (формат: [{'field': value}, ...])
    :param movement_data: Список движения товаров (формат: [{'field': value}, ...])
    :param stock_pay_user_data: Список остатка денежных средств сотрудников (формат: [{'field': value}, ...])
    """
    try:
        os.makedirs(REPORT_FOLDER, exist_ok=True)  # Создаем папку, если ее нет

        # Создаем DataFrame для остатков
        stock_df = pd.DataFrame(stock_data)

        # Создаем DataFrame для движения
        movement_df = pd.DataFrame(movement_data)

        stock_pay_user_df = pd.DataFrame(stock_pay_user_data)

        # Создаем общий файл Excel с двумя листами
        report_file = os.path.join(REPORT_FOLDER, "warehouse_report.xlsx")
        with pd.ExcelWriter(report_file, engine="openpyxl") as writer:
            stock_df.to_excel(writer, sheet_name="Stock", index=False)
            movement_df.to_excel(writer, sheet_name="Movements", index=False)
            stock_pay_user_df.to_excel(writer, sheet_name="Accounts Balances", index=False)

        return report_file
    except Exception as e:
        raise ValueError(f"Ошибка при генерации Excel отчета: {str(e)}")
