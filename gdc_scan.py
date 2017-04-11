#!/usr/bin/env python

import os
import json
import argparse
import requests
from pprint import pformat, pprint

URL_BASE="https://gdc-api.nci.nih.gov/"
LEGACY_BASE="https://gdc-api.nci.nih.gov/legacy/"
# URL_BASE="https://gdc-api.nci.nih.gov/v0/"
# LEGACY_BASE="https://gdc-api.nci.nih.gov/v0/legacy/"

PROJECTS="projects"
FILES="files"
CASES="cases"
ANNOTATIONS="annotations"

ENDPOINTS=[
    PROJECTS,
    FILES,
    CASES,
    ANNOTATIONS
]

def merge(*dicts):
    merged = {}
    for dict in dicts:
        merged.update(dict)
    return merged

# example filter --------------------
# {'and' [{'in': {'files.access': ['open']}}, {'in': {'files.data_format': ['MAF']}}]}

def expand_filter(d):
    op = d.keys()[0]
    content = d[op]
    if isinstance(content, list):
        content = map(expand_filter, content)
    else:
        field = content.keys()[0]
        value = content[field]
        content = {'field': field, 'value': value}
    return {'op': op, 'content': content}

def gdc_request(endpoint, params={}, legacy=False):
    base = (LEGACY_BASE if legacy else URL_BASE)
    url = base + endpoint
    default = {'size': 100, 'expand': []}
    all_params = merge(default, params)
    all_params['expand'] = ','.join(all_params['expand'])
    if 'filters' in all_params:
        all_params['filters'] = json.dumps(expand_filter(all_params['filters']))
    if 'fields' in all_params:
        all_params['fields'] = ','.join(all_params['fields'])

    print(url)
    print(str(all_params))
    request = requests.get(url, params=all_params)
    return request.json()

def gdc_paginate(endpoint, params={}, legacy=False, key='hits'):
    response = gdc_request(endpoint, params=params, legacy=legacy)
    if 'data' in response:
        data = response['data']
        for h in data[key]:
            if isinstance(data[key], list):
                yield h
            else:
                yield (h, data[key][h])

        while not 'size' in params and 'pagination' in data and data['pagination']['size'] > 0 and data['pagination']['page'] < data['pagination']['pages']:
            params['from'] = data['pagination']['from'] + data['pagination']['count']
            response = gdc_request(endpoint, params=params, legacy=legacy)
            data = response['data']

            for h in data[key]:
                if isinstance(data[key], list):
                    yield h
                else:
                    yield (h, data[key][h])
    elif 'message' in response:
        print('failure')
        print(response.keys())
        print(response['message'])
    
def build_conditions(args):
    conditions = [{'in': {'files.access': ['open']}}]

    if args.format:
        conditions.append({'in': {'files.data_format': [args.format]}})
    if args.type:
        conditions.append({'in': {'files.data_type': args.type.split(',')}})
    if args.project:
        conditions.append({'in': {'files.cases.project.project_id': [args.project]}})

    return {'and': conditions}

def facets(endpoint, field, legacy=False):
    result = {}
    params = {'facets': field, 'size': 0}
    response = gdc_request(endpoint, params=params, legacy=legacy)
    data = response['data']
    if 'aggregations' in data:
        aggregations = response['data']['aggregations']

        for key in aggregations:
            result[key] = {}
            for value in aggregations[key]['buckets']:
                result[key][value['key']] = value['doc_count']

        return result
    elif 'hits' in data:
        print(data['hits'][0].keys())

def project_list(args):
    for a in gdc_paginate(PROJECTS, legacy=args.legacy):
        print(a['project_id'])

CASE_FIELDS = [
    'project.name',
    'project.project_id',
    'project.primary_site',
    'submitter_id',
    'submitter_sample_ids'
]

CASE_EXPANSIONS = [
    'annotations',
    'demographic',
    'family_histories',
    'files',
    'diagnoses',
    'exposures',
    'project',
    'samples',
    'summary'
]

CASE_FILE_FIELDS = [
    'files.cases.project.project_id',
    'files.cases.samples.sample_id',
    'files.cases.samples.submitter_id',
    'files.cases.samples.sample_type',
    'files.cases.samples.sample_type_id',
    'files.data_type',
    'files.file_id',
    'files.file_name',
    'files.submitter_id',
    'files.type',
    'case_id'
]
        
def case_list(args):
    if args.id:
        case = gdc_request(os.path.join(CASES, args.id), params={'expand': CASE_EXPANSIONS}, legacy=args.legacy)
        print(pformat(case))
    else:
        for case in gdc_paginate(CASES, params={'fields': CASE_FIELDS}, legacy=args.legacy):
            print json.dumps(case)

def select_keys(m, keys):
    return {key: m[key] for key in keys}

def case_files(args):
    tree = {}
    params = {
        # 'size': 1,
        'expand': ['files','samples'],
        'fields': CASE_FILE_FIELDS
    }

    for case in gdc_paginate(CASES, params=params, legacy=args.legacy):
        case_id = case['case_id']
        print case_id
        for file in case['files']:
            if file['data_type'] == args.type:
                entry = select_keys(file, ['file_id', 'file_name'])
                entry['samples'] = file['cases'][0]['samples']
                entry['case_id'] = case_id
                tree[entry['file_name']] = entry

    return tree

def output_case_files(args):
    print(json.dumps(case_files(args), indent=2, sort_keys=True))
        
def process_files(args, process=lambda file: None):
    conditions = build_conditions(args)
    params={
        'expand': ['cases.samples.submitter_id'],
        'filters': conditions
    }

    if args.size:
        params['size'] = args.size

    files = []
    for file in gdc_paginate(FILES, params=params, legacy=args.legacy):
        files.append(file)
        process(file)

    return files

def download_file(file_name, file_id, legacy=False):
    try:
        print('downloading ' + file_name)
        base = LEGACY_BASE if legacy else URL_BASE
        r = requests.get(base + 'data' + '/' + file_id, stream=True)
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

    except Exception as e:
        print(str(e))

def download_recent(file_name, file_id, legacy=False):
    if not os.path.exists(file_name):
        download_file(file_name, file_id, legacy=legacy)

def file_list(args):
    if args.id:
        params = {'expand': ['cases','cases.samples']}
        file = gdc_request(os.path.join(FILES, args.id), params=params, legacy=args.legacy)
        print(pformat(file))
    else:
        # process_files(args, process=lambda m: pprint([m['file_name'], m['file_id']]))
        key = args.key if args.key else 'file_name'
        parts = key.split(',')
        files = process_files(args)
        pared = map(lambda file: select_keys(file, parts), files)
        print(json.dumps(pared))

def file_download(args):
    if args.id:
        download_file(args.id + '.out', args.id, legacy=args.legacy)
    else:
        process_files(args, process=lambda f: download_recent(f['file_name'], f['file_id'], legacy=args.legacy))

def case_facets(args):
    result = facets(CASES, args.attribute, legacy=args.legacy)
    print(json.dumps(result))

def file_facets(args):
    result = facets(FILES, args.attribute, legacy=args.legacy)
    print(json.dumps(result))

def mapping(endpoint, args):
    response = gdc_request(os.path.join(endpoint, '_mapping'))['fields']
    response.sort()

    print(pformat(response))

METHODS = {
    PROJECTS : {
        'list' : {
            'func' : project_list,
        },

        'mapping' : {
            'func' : lambda args: mapping(PROJECTS, args)
        }
    },

    CASES : {
        'list' : {
            'func' : case_list,
            'opts' : [
                ['--id', {'type': str}],
                ['--project', {'type': str}]
            ]
        },

        'facets' : {
            'func' : case_facets,
            'args' : ['attribute']
        },

        'files': {
            'func' : output_case_files,
            'args' : ['type']
        },

        'mapping' : {
            'func' : lambda args: mapping(CASES, args)
        }
    },

    FILES : {
        'list' : {
            'func' : file_list,
            'opts' : [
                ['--format', {'type': str}],
                ['--id', {'type': str}],
                ['--project', {'type': str}],
                ['--size', {'type': int}],
                ['--type', {'type': str}],
                ['--key', {'type': str}]
            ]
        },

        'facets' : {
            'func' : file_facets,
            'args' : ['attribute']
        },

        'download' : {
            'func' : file_download,
            'opts' : [
                ['--format', {'type': str}],
                ['--id', {'type': str}],
                ['--project', {'type': str}],
                ['--size', {'type': int}],
                ['--type', {'type': str}]
            ]
        },

        'mapping' : {
            'func' : lambda args: mapping(FILES, args)
        }
    }
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    sub_parser = parser.add_subparsers()
    for m in METHODS:
        parser_m = sub_parser.add_parser(m)
        sub_parser_m = parser_m.add_subparsers()
        for k,v in METHODS[m].items():
            parser_k = sub_parser_m.add_parser(k)
            if 'args' in v:
                parser_k.add_argument(*v['args'])
            if 'opts' in v:
                for opt in v['opts']:
                    parser_k.add_argument(opt[0], **opt[1])
            parser_k.add_argument('--legacy', action='store_true')
            parser_k.set_defaults(func=v['func'])

    args = parser.parse_args()
    
    args.func(args)
