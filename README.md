# Lambda to BigQuery

AWS LambdaからGoogle Cloud BigQueryにデータを挿入するためのLambda関数です。

## 概要

このLambda関数は以下の機能を提供します：
- BigQueryデータセットの作成
- 日付サフィックス付きテーブルの作成
- テストデータの挿入

## 前提条件

以下のツールがインストールされている必要があります：

1. **AWS CLI**
   - インストール方法: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
   - 設定方法: `aws configure`を実行し、認証情報を設定

2. **AWS SAM CLI**
   - インストール方法: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html

3. **Python 3.12**
   - インストール方法: https://www.python.org/downloads/

## 事前準備

### Google Cloud側の設定
1. **サービスアカウントの作成**:
   - IAMと管理 > サービスアカウントに移動
   - サービスアカウントを作成:
     - サービスアカウント名: `lambda-to-bigquery`
     - ロール: `BigQuery 管理者`

2. **認証情報のダウンロード**:
   - 作成したサービスアカウントの詳細画面に移動
   - 鍵 > キーを追加 > 新しい鍵を作成
   - キーのタイプ: JSON
   - 作成をクリックしJSONファイルをダウンロード

### AWS側の設定
1. **Parameter Storeの設定**:
   - AWS Systems Managerコンソールを開く
   - 左メニューからパラメータストアを選択
   - パラメータの作成をクリック
   - 以下の項目を入力:
     - 名前: `/gcp/bigquery/credentials`
     - タイプ: `SecureString`
     - 値: ダウンロードしたGCPサービスアカウントのJSONキーの内容をそのまま貼り付け
   - パラメータの作成をクリック

## デプロイ方法

1. リポジトリのクローン
```bash
git clone https://github.com/kawabata-mcl/lambda-to-bigquery.git
cd lambda-to-bigquery
```

2. 依存パッケージのインストール
```bash
# Lambda Layer用の依存パッケージをインストール
mkdir -p layer/python
pip install -r src/requirements.txt -t layer/python
```

3. SAMでビルド
```bash
sam build
```

4. SAMでデプロイ
```bash
sam deploy --guided
```

初回デプロイ時は対話形式で以下の項目を設定します：
- Stack Name [sam-app]: lambda-to-bigquery
- AWS Region [ap-northeast-1]: デプロイするリージョン（例：ap-northeast-1）
- Parameter ParameterName [/gcp/bigquery/credentials]: enterを押す
- Confirm changes before deploy [y/N]: y
- Allow SAM CLI IAM role creation [Y/n]: Y
- Disable rollback [y/N]: y
- Save arguments to configuration file [Y/n]: Y
- SAM configuration file [samconfig.toml]: enterを押す
- SAM configuration environment [default]: enterを押す

changesetを実行するか確認されます：
- Deploy this changeset? [y/N]: y

2回目以降は `sam deploy` のみで良いです。

## テスト実行
1. AWS CLIでデプロイ済みのLambdaをテスト
```bash
# テストイベントを使用して実行
aws lambda invoke \
  --function-name lambda-to-bigquery \
  --payload file://events/test-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# 実行結果を確認
cat response.json
```

2. AWSコンソールでのテスト
   1. Lambdaのコンソールを開く
   2. `lambda-to-bigquery`のLambda関数を選択
   3. テストタブを選択し、以下を設定
      - イベント名: `test`
   4. `テスト`をクリック
   5. `実行中の関数: 成功`が表示されれば成功です

### 実行結果の確認

CloudWatch Logsからログを確認できます

## ディレクトリ構成

```
lambda-to-bigquery/
├── src/
│   ├── lambda_function.py
│   └── requirements.txt
├── events/
│   └── test-event.json
├── template.yaml
└── README.md
```

## 作成されるリソース

### Google Cloud リソース

1. BigQueryデータセット
   - 名前: test_data_set
   - ロケーション: US

2. BigQueryテーブル
   - 名前: test_table_YYYYMMDD
   - スキーマ:
     - user_id (STRING)
     - name (STRING)

### AWS リソース

1. Lambda関数
   - 名前: lambda-to-bigquery
   - ランタイム: Python 3.12
   - メモリ: 128 MB
   - タイムアウト: 60秒
   - 実行ロール: 自動生成

2. IAMロール
   - 管理ポリシー:
     - AWSLambdaBasicExecutionRole
   - インラインポリシー:
     - SSMパラメータストアの読み取り権限

3. Lambda Layer
   - 名前: bigquery-layer
   - 説明: Layer for google-cloud-bigquery
   - 互換ランタイム: Python 3.12
