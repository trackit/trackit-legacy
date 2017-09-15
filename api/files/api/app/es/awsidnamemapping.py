import elasticsearch_dsl as dsl


class AWSIdNameMapping(dsl.DocType):
    class Meta:
        index = 'awsidnamemapping'
    key = dsl.String(index='not_analyzed')
    rid = dsl.String(index='not_analyzed')
    name = dsl.String(index='not_analyzed')
    date = dsl.Date(format='date_optional_time||epoch_millis')

    @classmethod
    def get_id_name_mapping(cls, key):
        s = cls.search()
        s = s.query('match', key=key).sort('-date')
        res = {}
        for hit in s.scan():
            if hit.rid not in res:
                res[hit.rid] = hit.name
        return res
