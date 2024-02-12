from datetime import datetime

import calendar


class MyCalendar(calendar.LocaleHTMLCalendar):
    def __init__(self, username: str, linked_date: dict):
        calendar.LocaleHTMLCalendar.__init__(self, firstweekday=6, locale='ja_jp')

        self.username = username
        self.linked_date = linked_date  # dict{'datetime': done}

    def formatmonth(self, theyear: int, themonth: int, withyear: bool = True) -> str:
        v = []
        a = v.append
        a('<table class="table table-bordered table-sm" style="table-layout: fixed;">')
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week, theyear, themonth))
            a('\n')
        if len(self.monthdays2calendar(theyear, themonth)) == 5:
            for _ in range(7):
                a(self.formatday(0, 0, theyear, themonth))
                a('\n')
        a('</table><br>')
        a('\n')
        return ''.join(v)

    def formatweek(self, theweek: int, theyear: int, themonth: int) -> str:
        s = ''.join(self.formatday(d, wd, theyear, themonth) for (d, wd) in theweek)
        return '<tr>{}</tr>'.format(s)

    def formatday(self, day: int, weekday: int, theyear: int, themonth: int) -> str:
        if day == 0:
            return '<td style="background-color: #eeeeee;">&nbsp;</td>'
        else:
            html = '<td class="text-center {highlight}"><a href="{url}" style="color: {text};">{day}</a></td>'
            text = 'blue'
            highlight = ''

            # 予定があれば強調
            date = datetime(year=theyear, month=themonth, day=day)
            date_str = date.strftime('%Y%m%d')
            if date_str in self.linked_date:
                if self.linked_date[date_str]:
                    highlight = 'bg-success'
                    text = 'white'
                elif date < datetime.now():
                    highlight = 'bg-secondary'
                    text = 'white'
                else:
                    highlight = 'bg-warning'

            return html.format(
                url='/todo/{}/{}/{}/{}'.format(self.username, theyear, themonth, day),
                text=text,
                day=day,
                highlight=highlight
            )
