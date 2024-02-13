import re

import pandas
from bokeh import embed, resources
from bokeh.models import Range1d, LinearAxis, LabelSet, ColumnDataSource
from bokeh.plotting import figure
from django.db.models import Q, Count, Avg
from django.http import HttpRequest, HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.datetime_safe import datetime
from django.utils.safestring import mark_safe

from bank.models import TanRequest
from report.get_recharges import get_recharges
from .models import Transaction, FeeEntry
from io import StringIO
import member_report
from django.urls import reverse


def index(request):
    return render(request, 'index.html', {})


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
    p1.sizing_mode = 'scale_width'
    p1.height = 300
    p1.grid.grid_line_alpha = 0.3
    p1.xaxis.axis_label = 'Datum'
    p1.yaxis.axis_label = 'Summe'

    p1.step(dates, sums, color='#22aa22', legend='Summe', line_width=3)
    p1.line([dates[0], dates[-1]], [0, 0], color='#aa0000', line_width=1)
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


def members_per_month(request: HttpRequest):
    members_per_month = FeeEntry.objects.values('month').order_by('month')\
        .annotate(count=Count('month'))
    df_members = pandas.DataFrame.from_dict(members_per_month)
    df_members['month'] = df_members['month'].map(
        lambda m: m.strftime('%Y-%m'))
    df_members['count_text'] = df_members['count'].map(
        lambda p: '{:.0f}'.format(p))

    df_members = df_members.iloc[1:-1]

    member_fees = FeeEntry.objects.values('month').order_by('month') \
        .annotate(fee=Avg('fee'))
    df_fees = pandas.DataFrame.from_dict(member_fees)
    df_fees['month'] = df_fees['month'].map(lambda m: m.strftime('%Y-%m'))
    df_fees['fee_text'] = df_fees['fee'].map(lambda p: '{:.0f}'.format(p))

    p1: Figure = figure(
        title="Member pro Monat",
        x_range=df_members['month'],
        tooltips=[("Monat", "@month"), ("Anzahl", "@count")],
        plot_height=300
    )
    p1.sizing_mode = 'scale_width'

    p1.step(x='month',
            color='navy',
            line_width=3,
            source=df_members,
            y='count',
            legend="Count of Members (paid fees)"
            )

    p1.extra_y_ranges = {"fee_range": Range1d(
        start=0, end=df_fees['fee'].astype(float).max() + 5)}
    p1.add_layout(LinearAxis(y_range_name="fee_range"), 'right')
    p1.step(
        x='month',
        y='fee',
        color='firebrick',
        source=df_fees,
        line_width=2,
        y_range_name="fee_range",
        legend="Average Fee per member"
    )

    labels = LabelSet(x='month', y='fee', text='fee_text', level='glyph',
                      x_offset=-10, y_offset=10, source=ColumnDataSource(df_fees),
                      text_font_size="9pt",
                      y_range_name="fee_range"
                      )
    p1.add_layout(labels)

    labels = LabelSet(x='month', y='count', text='count_text', level='glyph',
                      x_offset=-15, y_offset=10, source=ColumnDataSource(df_members),
                      text_font_size="9pt"
                      )
    p1.add_layout(labels)

    p1.y_range.start = 0
    p1.y_range.end = df_members['count'].max() + 4
    p1.x_range.range_padding = 0.1
    p1.xaxis.axis_label = "Monat"
    p1.xaxis.major_label_orientation = 1.2
    # p1.outline_line_color = None
    p1.legend.location = 'bottom_right'

    html = embed.file_html(p1, resources.CDN, "Member pro Monat")

    return render(request, 'graph.html', {'html': mark_safe(html)})


def member_report_view(request: HttpRequest):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/admin/login')

    output = StringIO()
    member_report.main([], to=output, months=36)
    output = output.getvalue()
    return render(request, 'member_report.html', {'report': mark_safe(output)})

# @basicauth(realm="Parole?")


def recharges(request: HttpRequest):
    all = get_recharges()
    return JsonResponse(all)


def admin_tan(request: HttpRequest):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/admin/login')

    if 'action' in request.POST and request.POST['action'] == 'number':
        return JsonResponse({'number': TanRequest.active_requests().count()})

    if 'tan' in request.POST:
        tan = request.POST['tan']
        date = request.POST['date']
        tan = re.sub(r'[^a-zA-Z0-9]', "", tan)
        tan_request = TanRequest.objects.get(
            pk=datetime.fromtimestamp(float(date), tz=timezone.utc))
        if tan_request.answer or tan_request.expired:
            return render(request, 'admin_tan.html', {'error': "TAN request expired"})
        tan_request.answer = tan
        tan_request.save()

        return render(request, 'admin_tan.html', {'tan': tan})

    tan_request = TanRequest.active_request()
    return render(request, 'admin_tan.html', {
        'tan_request': tan_request,
        'id': tan_request.date.timestamp() if tan_request else None
    })
