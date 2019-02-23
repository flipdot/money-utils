import pandas
from bokeh import embed, resources
from bokeh.plotting import figure, Figure
from django.db.models import Q, Count
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from report.decorators import basicauth
from report.get_recharges import get_recharges
from .models import Transaction, FeeEntry


def index(request):
    context = {
    }
    return render(request, 'index.html', context)


def drinks(request: HttpRequest):
    txs = drinks_transactions()
    sum = 0
    dates = []
    sums = []
    txs_transformed = []
    for tx in txs:
        sum += tx.amount
        dates.append(tx.date)
        sums.append(sum)
        txs_transformed.append({
            'sum': sum,
            'date': tx.date.isoformat(),
            'amount': tx.amount,
            'purpose': tx.purpose,
            'applicant': tx.applicant_name
        })

    p1: Figure = figure(x_axis_type="datetime", title="Getränkeverkauf")
    p1.sizing_mode='scale_width'
    p1.height = 400
    p1.grid.grid_line_alpha=0.3
    p1.xaxis.axis_label = 'Datum'
    p1.yaxis.axis_label = 'Summe'

    p1.line(dates, sums, color='#22aa22', legend='Summe', line_width=3)
    p1.line([dates[0], dates[-1]], [0,0], color='#aa0000', line_width=1)
    p1.legend.location = "top_left"

    html = embed.file_html(p1, resources.CDN, "Getränkeverkauf")
    context = {
        'html': mark_safe(html),
        'txs': txs_transformed if request.user.is_staff else None
    }
    return render(request, 'drinks.html', context)


def drinks_transactions():
    tx = Transaction.objects\
        .filter(
            Q(purpose__contains='edeka')
            | Q(applicant_name__contains='edeka')
            | Q(purpose__startswith='drinks ')
            | Q(purpose__contains='sb-einzahlung')
            | Q(purpose__contains='UNGEZaeHLTES KLEINGELD')
            | Q(purpose__contains='EINNAHMEN GETRAENKEVERKAUF')
    ).order_by('date')
    return tx


def member(request: HttpRequest):
    members_per_month = FeeEntry.objects.values('month').order_by('month')\
        .annotate(count=Count('month'))
    df = pandas.DataFrame.from_dict(members_per_month)
    df['month'] = df['month'].map(lambda m: m.strftime('%Y-%m'))

    p1: Figure = figure(title="Member pro Monat", x_range=df['month'],
        tooltips=[("Monat", "@month"), ("Anzahl", "@count")])
    p1.sizing_mode='scale_width'

    p1.vbar(x='month', width=0.8, source=df, bottom=0, top='count', fill_color='#9999ff', line_color=None, )

    p1.y_range.start = 0
    #p1.x_range.start = members_per_month[0]['month']
    #p1.x_range.end = date.today().replace(day=1).strftime("%Y-%m")
    p1.x_range.range_padding = 0.05
    p1.xaxis.axis_label = "Monat"
    p1.xaxis.major_label_orientation = 1.2
    p1.outline_line_color = None

    html = embed.file_html(p1, resources.CDN, "Member pro Monat")

    return render(request, 'graph.html', {'html': mark_safe(html)})

@basicauth(realm="Parole?")
def recharges(request: HttpRequest):
    all = get_recharges()
    return JsonResponse(all)
