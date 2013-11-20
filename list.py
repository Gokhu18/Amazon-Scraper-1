#!/usr/bin/python

import os, sys, datetime, argparse

from operator import itemgetter

from app.pricefuncs import price_int_to_str, str_align
from app.db import *
session = None

def best_deals(products, number=10):
    return sorted(products, key=itemgetter('price_diff'), reverse=True)[0:number]

def cheapest_deals(products, number=8):
    return sorted(products, key=itemgetter('price_sale'))[0:number]

def print_products(title, group, products, num=8):
    print('-'*80)
    print('%s in %s' % (title, group))
    print('-'*80)
    
    for p in products:
        print('$%s$%s%s - %s' % (
            str_align(price_int_to_str(p['price_sale']), 8, mode='suffix'),
            str_align(price_int_to_str(p['price_regular']), 8, mode='suffix'),
            str_align('($'+price_int_to_str(p['price_diff'])+')', 8, mode='suffix'),
            p['print_title']
        )
    )

def main():
    global session
    
    functions = [
        ('Cheapest Deals', cheapest_deals),
        ('Best Deals', best_deals),
    ]
    
    parser = argparse.ArgumentParser()
    parser.add_argument(    '-n', '--number',
                            help='Number of items per group to print',
                            type=int,
                            default=10)
    
    args = parser.parse_args()
    print_number = args.number
    
    if args.number is not None:
        print_number = args.number
    
    manager = SessionManager('sqlite:///products.db')
    session = manager.session

    groups = session.query(ProductGroup)\
                    .order_by(ProductGroup.name)

    overall = {}
    for group in groups:
        products = []
        queryobj = session.query(Product)\
                          .filter(Product.group_id == group.id)\
                          .order_by(Product.title)

        for pr in queryobj:
            pp = session.query(ProductPrice)\
                        .filter(ProductPrice.product_id == pr.id)\
                        .order_by(ProductPrice.created.desc())\
                        .first()

            item = {
                'title': pr.title,
                'print_title': pr.title,
                'price_sale': pp.price_sale,
                'group_name': group.name
            }
            
            if pp.price_regular < pp.price_sale:
                item['price_diff'] = 0
                item['price_regular'] = pp.price_sale
            else:
                item['price_diff'] = pp.price_regular - pp.price_sale
                item['price_regular'] = pp.price_regular

            products.append(item)

        for title, fn in functions:
            _sorted = fn(products, args.number)
            print_products(title, group.name, _sorted)
            
            if title not in overall:
                overall[title] = _sorted
            else:
                overall[title].extend(_sorted)
    
    for title, fn in functions:
        _sorted = fn(overall[title])[0:args.number]
        for i in _sorted:
            i['print_title'] = '%s (%s)' % (i['title'], i['group_name'])
        
        print_products(title, 'Overall', _sorted)

    sys.exit(0)

if __name__ == '__main__':
    main()
