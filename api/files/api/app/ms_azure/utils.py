def meter_info_to_dict(infos):
    res = {
        'meter_id': infos.meter_id,
        'meter_name': infos.meter_name,
        'meter_category': infos.meter_category,
        'meter_sub_category': infos.meter_sub_category,
        'unit': infos.unit,
        'meter_rates': infos.meter_rates,
        'effective_date': infos.effective_date.isoformat(),
        'included_quantity': infos.included_quantity
    }
    return res
