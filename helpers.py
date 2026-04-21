def rank_list(data: list[dict], target_field: str) -> list[dict]:
    """
    Add a rank value to an ordered list, based on the value of field 'target'.
    Starts at 1 and only counts up for a higher target value.
    """
    rank = 1
    for i, item in enumerate(data):
        try:
            if i > 0 and item[target_field] != data[i - 1][target_field]:
                rank += 1
        except KeyError as e:
            raise KeyError("target field in rank_list not found in dict key")

        item["rank"] = rank
    return data