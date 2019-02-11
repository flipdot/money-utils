from django.db.models import Q
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

import numpy as np
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file, Figure
from bokeh import plotting, embed, resources
# Create your views here.
from django.template import loader
from django.utils.safestring import mark_safe


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
    from .models import Transaction
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
