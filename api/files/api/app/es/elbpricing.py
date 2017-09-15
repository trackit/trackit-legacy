import elasticsearch_dsl as dsl


class ELBPricing(dsl.DocType):
    class Meta:
        index = 'elbpricing'
    region_machine_friendly = dsl.String(index='not_analyzed')
    region_human_friendly = dsl.String(index='not_analyzed')
    price_per_hour = dsl.String(index='not_analyzed')
    price_per_GB = dsl.String(index='not_analyzed')
