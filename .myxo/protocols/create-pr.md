---
name: create-pr
description: Pull Request 作成手順
triggers:
  - pr
  - pull-request
  - create-pr
---

## Steps
1. 現在のブランチとベースブランチを確認する
2. 変更差分を確認しステージする
3. コミットメッセージを作成する
4. リモートにプッシュする
5. `gh pr create` で PR を作成する

## Rules
- PR タイトルは70文字以内にする
- body に Summary セクションを含める
- Test plan は PR コメントとして追加する
- base ブランチは develop を使用する
- Closes #XX で関連 Issue を紐付ける
