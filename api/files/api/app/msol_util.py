from base64 import urlsafe_b64encode
from hashlib import sha256
from datetime import datetime, time
from datetime import timedelta

# From a list of "old" elements and a list of "new" elements, build a list of
# "added" elements and a list of "deleted" elements.
def content_diff(old, new, comparator=(lambda a, b: a == b)):
    old = list(old)
    new = list(new)
    added =   filter(lambda n: not any(map(lambda o: comparator(o, n), old)), new)
    deleted = filter(lambda o: not any(map(lambda n: comparator(o, n), new)), old)
    return added, deleted

# Returns the index of the first truthy elemnt of the "predicate" iterator, or
# None.
def index_of(predicate):
    return next((i for i, p in enumerate(predicate) if p), None)

def checksum(*args):
    acc = sha256()
    for arg in args:
        acc.update(arg)
    return urlsafe_b64encode(acc.digest()[0:30])

def day_allocations(start, stop):
    if not start or not stop:
        return

    if (stop - start).total_seconds() <= 0:
        return

    days = []
    now = start
    while now < stop:
        tomorrow = now + timedelta(days=1)
        tomorrow = datetime.combine(tomorrow, time(0))
        if tomorrow > stop:
            tomorrow = stop
        days.append((now.date(), (tomorrow - now).total_seconds()))
        now = tomorrow

    total_seconds = sum(secs for _, secs in days)

    for day, secs in days:
        yield day, secs / total_seconds

def get_next_update_estimation_message_aws(accounts, update_interval_hours):
    if type(accounts) is not list:
        accounts = [accounts]
    all_accounts_fetched = True
    last_scheduled_update = 0
    for account in accounts:
        if not account.last_fetched or account.last_fetched - datetime.now() < timedelta(minutes=30):
            all_accounts_fetched = False
        next_update_delta = timedelta(hours=update_interval_hours) if not account.last_fetched else account.last_fetched + timedelta(hours=update_interval_hours) - datetime.now()
        next_update, remainder = divmod(next_update_delta.seconds, 3600)
        if next_update < 1:
            next_update = 1
        if next_update > last_scheduled_update:
            last_scheduled_update = next_update
    if len(accounts) == 1:
        if accounts[0].error_status == 'bad_key':
            return "The credentials you entered are incorrect. The next data processing will take place in {} hour{}".format(last_scheduled_update, '' if last_scheduled_update <= 1 else 's')
        elif accounts[0].error_status == 'billing_report_error':
            return "There is an error in your billing report setup. The next data processing will take place in {} hour{}".format(last_scheduled_update, '' if last_scheduled_update <= 1 else 's')
        elif accounts[0].error_status == 'no_such_bucket':
            return "The billing bucket you specified does not exist. The next data processing will take place in {} hour{}".format(last_scheduled_update, '' if last_scheduled_update <= 1 else 's')
        elif accounts[0].error_status == 'processing_error':
            return "We encountered an error while processing this key. The next data processing will take place in {} hour{}".format(last_scheduled_update, '' if last_scheduled_update <= 1 else 's')
    if all_accounts_fetched:
        return "No data available. The next data processing will take place in {} hour{}".format(last_scheduled_update, '' if last_scheduled_update <= 1 else 's')
    else:
        return "Your data are still processing. The data will be available in {} hour{}".format(last_scheduled_update, '' if last_scheduled_update <= 1 else 's')
