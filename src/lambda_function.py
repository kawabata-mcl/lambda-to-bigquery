"""
BigQueryテーブル作成・データ挿入Lambda関数

このスクリプトは、AWS LambdaからGCP BigQueryにアクセスし、
日付サフィックス付きのテーブルを作成してデータを挿入します。

Requirements:
    - google-cloud-bigquery
    - boto3

Environment Variables:
    - PARAMETER_NAME: AWS Parameter Storeのパラメータ名
"""

import os
import json
import time
import boto3
from google.cloud import bigquery
from datetime import datetime
from typing import List, Dict, Any

def get_credentials() -> Dict[str, Any]:
    """
    AWS Parameter Storeから認証情報を取得します。

    Returns:
        Dict[str, Any]: GCPサービスアカウントの認証情報
    """
    ssm = boto3.client('ssm')
    parameter_name = os.environ.get('PARAMETER_NAME', '/gcp/bigquery/credentials')
    parameter = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return json.loads(parameter['Parameter']['Value'])

def create_dataset_if_not_exists(client: bigquery.Client, dataset_id: str) -> None:
    """
    指定されたデータセットが存在しない場合、新しいデータセットを作成します。

    Args:
        client: BigQueryクライアント
        dataset_id: 作成するデータセットのID
    """
    try:
        client.get_dataset(dataset_id)
        print(f"データセット {dataset_id} は既に存在します。")
    except Exception as e:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"  # データセットのロケーションを設定
        client.create_dataset(dataset)
        print(f"データセット {dataset_id} を作成しました。")

def create_table_if_not_exists(client: bigquery.Client, table_name: str) -> None:
    """
    指定されたテーブルが存在しない場合、新しいテーブルを作成します。

    Args:
        client: BigQueryクライアント
        table_name: 作成するテーブルの完全修飾名
    """
    try:
        client.get_table(table_name)
        print(f"テーブル {table_name} は既に存在します。")
    except Exception as e:
        schema = [
            bigquery.SchemaField("user_id", "STRING"),
            bigquery.SchemaField("name", "STRING"),
        ]
        table = bigquery.Table(table_name, schema=schema)
        client.create_table(table)
        print(f"テーブル {table_name} を作成しました。")
        print("テーブルの作成完了を待機中...")
        time.sleep(10)  # テーブル作成完了を待つために10秒待機
        print("待機完了")

def insert_data(client: bigquery.Client, table_name: str, rows: List[Dict[str, str]]) -> None:
    """
    テーブルにデータを挿入します。

    Args:
        client: BigQueryクライアント
        table_name: テーブルの完全修飾名
        rows: 挿入するデータの行のリスト
    """
    errors = client.insert_rows_json(table_name, rows)
    if errors:
        raise Exception(f"データの挿入中にエラーが発生しました: {errors}")
    print("データが正常に挿入されました。")

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda関数のメインハンドラー

    Args:
        event: Lambda関数のイベントデータ
        context: Lambda関数のコンテキスト

    Returns:
        Dict[str, Any]: 実行結果
    """
    try:
        # BigQueryクライアントの作成
        credentials = get_credentials()
        client = bigquery.Client.from_service_account_info(credentials)

        # プロジェクトIDとデータセットIDの設定
        project_id = credentials.get('project_id')
        dataset_id = f"{project_id}.test_data_set"

        # データセットの作成
        create_dataset_if_not_exists(client, dataset_id)

        # テーブル名の生成
        today = datetime.now().strftime('%Y%m%d')
        table_name = f"{dataset_id}.test_table_{today}"

        # テーブルの作成
        create_table_if_not_exists(client, table_name)

        # テストデータの定義
        test_data = [
            {"user_id": "test001", "name": "テストユーザー1"},
            {"user_id": "test002", "name": "テストユーザー2"},
            {"user_id": "test003", "name": "テストユーザー3"},
            {"user_id": "test004", "name": "テストユーザー4"},
            {"user_id": "test005", "name": "テストユーザー5"},
        ]

        # データの挿入
        insert_data(client, table_name, test_data)

        return {
            'statusCode': 200,
            'body': json.dumps('処理が正常に完了しました。')
        }

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'エラーが発生しました: {str(e)}')
        }