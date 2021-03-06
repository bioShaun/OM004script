import click
import pandas as pd
import os
import glob
from omstools.utils.config import CLICK_CONTEXT_SETTINGS
from omstools.utils.config import MutuallyExclusiveOption


def merge_files(df_list, df0=None, method='left', by='index'):
    if df0 is None:
        df0 = df_list.pop(0)
        return merge_files(df_list, df0, method=method, by=by)
    elif df_list:
        df1 = df_list.pop(0)
        if by == 'index':
            new_df = pd.merge(df0, df1,
                              left_index=True,
                              right_index=True,
                              how=method)
            new_df.index.name = df0.index.name
        else:
            new_df = pd.merge(df0, df1,
                              how=method)
        return merge_files(df_list, df0=new_df,
                           method=method, by=by)
    else:
        return df0


@click.command(context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument(
    'file_and_columns',
    nargs=-1)
@click.argument(
    'output',
    nargs=1)
@click.option(
    '-nh',
    '--noheader',
    is_flag=True,
    help='Input tables without header.',
)
@click.option(
    '-bn',
    '--by_colname',
    is_flag=True,
    help='Merge tables by identical columns.',
    cls=MutuallyExclusiveOption,
    mutually_exclusive=['by_row'],
)
@click.option(
    '-bh',
    '--by_row',
    is_flag=True,
    help='Merge tables by row.',
    cls=MutuallyExclusiveOption,
    mutually_exclusive=['by_colname'],
)
@click.option(
    '-na',
    '--na_rep',
    default='0',
    help='Value to replace NA in merged table. [default: 0]'
)
@click.option(
    '--method',
    default='left',
    type=click.Choice(['left', 'right', 'outer', 'inner'])
)
@click.option(
    '--float_format',
    default=None
)
def main(file_and_columns, output, noheader, na_rep,
         by_colname, by_row, method, float_format):
    '''Merge Multi files by matched column
    '''
    # seperate files and columns
    if by_colname or by_row:
        table_dfs = [pd.read_table(each_file)
                     for each_file in file_and_columns]
        if by_colname:
            merged_df = merge_files(table_dfs, method=method, by='column')
        else:
            merged_df = pd.concat(table_dfs)
        merged_df.to_csv(output, sep='\t',
                         na_rep=na_rep, float_format=float_format,
                         index=False)
        return 1

    files = list()
    columns = list()
    for n, each in enumerate(file_and_columns):
        if '*' in each:
            each_files = glob.glob(each)
            files.extend(each_files)
        elif os.path.isfile(each):
            files.append(each)
        else:
            break
    file_num = len(files)
    para_num = len(file_and_columns)
    if n < para_num - 1:
        columns = [int(each) for each in file_and_columns[n:]]
    # simple check
    if file_num < 2:
        click.secho('File number must more than 2.', color='red')
        return 1
    else:
        if columns:
            if file_num != len(columns):
                click.secho(
                    'File number should equal to column number.', color='red')
                return 1
        else:
            columns = [1 for each in range(file_num)]
        # read files based on merging columns
        # if tables has header
        if noheader:
            df_list = [
                pd.read_table(files[i], index_col=columns[i] - 1,
                              header=None)
                for i in range(file_num)
            ]
        else:
            df_list = [
                pd.read_table(files[i], index_col=columns[i] - 1)
                for i in range(file_num)
            ]
        # merge files
        merged_df = merge_files(df_list, method=method)
        header = not noheader
        merged_df.to_csv(output, sep='\t', header=header,
                         na_rep=na_rep, float_format=float_format)
    return 1


if __name__ == '__main__':
    main()
