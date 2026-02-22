import json


class AggTrade:
    @staticmethod
    def get_message(row: list[str], symbol: str) -> dict[str, str]:
        agg_trade = {
            "agg_trade_id": int(row[0]),
            "price": float(row[1]),
            "quantity": float(row[2]),
            "first_trade_id": int(row[3]),
            "last_trade_id": int(row[4]),
            "ts_int": int(row[5]),
            "is_buyer_maker": row[6].strip().lower() == "true",
            "is_best_match": row[7].strip().lower() == "true",
            "symbol": symbol,
        }
        return {"key": symbol, "value": json.dumps(agg_trade)}
