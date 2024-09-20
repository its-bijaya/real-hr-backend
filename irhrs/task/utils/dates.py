"""@irhrs_docs"""
from dateutil.rrule import rrule, MONTHLY, DAILY, YEARLY
from datetime import timedelta
import calendar


def dates_for_efficiency_report(original_date, stop, condition):
    generated = []

    if condition == 'monthly':
        agg = list(rrule(freq=MONTHLY, dtstart=original_date.replace(day=1),
                         until=stop))
        agg[0] = original_date
        if agg[-1] != stop:
            agg.append(stop)
        for i, j in enumerate(agg, start=1):
            start = j.date()
            try:
                end = (agg[i].date() - timedelta(days=1)) if start.month != \
                                                             agg[i].month else \
                    agg[i].date()
            except IndexError:
                break

            if start.month == end.month:
                label = calendar.month_abbr[start.month]
            else:
                label = calendar.month_abbr[start.month] + '/' + \
                        calendar.month_abbr[end.month]
            generated.append({
                'start_date': start,
                'end_date': end,
                'label': label,
                'var': label
            })
    elif condition == 'yearly':
        agg = list(rrule(freq=YEARLY, dtstart=original_date.replace(day=1),
                         until=stop))
        agg[0] = original_date
        if agg[-1] != stop:
            agg.append(stop)
        for i, j in enumerate(agg, start=1):
            start = j.date()
            try:
                end = (agg[i].date() - timedelta(days=1)) if start.year != agg[
                    i].year else agg[i].date()
            except IndexError:
                break
            generated.append({
                'start_date': start,
                'end_date': end,
                'label': j.date().year,
                'var': j.date().year
            })
    else:
        agg = list(rrule(freq=DAILY, dtstart=original_date, until=stop))
        for i in agg:
            generated.append({
                'start_date': i.date(),
                'end_date': i.date(),
                'label': calendar.month_abbr[i.month] + ' ' + i.day.__str__(),
                'var': calendar.month_abbr[i.month] + i.day.__str__()
            })
    return generated
