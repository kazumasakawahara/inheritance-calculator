# 再転相続（さいてんそうぞく）

## 概要

再転相続とは、相続人が被相続人の相続について承認または放棄をしないまま死亡し、その相続人の相続人が被相続人の相続に関する承認・放棄の権利を承継する制度です（民法第896条）。

## 法的根拠

### 民法第896条（相続人の相続）

> 相続人が、相続の承認又は放棄をしないで死亡したときは、その者の相続人が、
> 自己の相続権の範囲内で、被相続人の権利義務を承継する。

## 発生要件

再転相続が発生するには、以下の要件を満たす必要があります：

1. **第1次相続が開始していること**
   - 被相続人Aが死亡し、相続が開始している

2. **第1次相続人が遺産分割前に死亡していること**
   - 第1次相続人Bが、Aの遺産分割をしないまま死亡している
   - 遺産分割協議がまだ成立していないこと

3. **第2次相続が開始していること**
   - Bの死亡により、Bを被相続人とする第2次相続が開始している

4. **承認・放棄の選択がされていないこと**
   - Bが、Aの相続について承認も放棄もしていない状態であること

## 実装上の特徴

### 1. 相続分の計算

再転相続における相続分は、**第2次相続の法定相続分に基づいて按分**されます。

#### 例: 配偶者と子がいる場合

```
第1次相続: A（被相続人）→ B（子、遺産分割前に死亡）
第2次相続: B（被相続人）→ C（配偶者）、D（子）、E（子）

Bの相続分（100%）の分配:
- C（配偶者）: 1/2  (民法900条1号: 配偶者1/2)
- D（子）    : 1/4  (民法900条1号: 子1/2を2人で分割)
- E（子）    : 1/4
```

### 2. 判例による制約（最高裁昭和63年6月21日判決）

再転相続においては、以下の制約があります：

**第2次相続を放棄した者は、第1次相続のみを承認することができない**

#### 理由

- 第2次相続（Bの相続）を放棄することで、Bから承継する権利を全て放棄している
- したがって、Bが持っていたAの相続権も承継できない
- 論理的に、第1次相続だけを承認することは矛盾する

#### 許容される選択肢

1. **両方の相続を承認** ✅
   - 第1次相続（Aの相続）: 承認
   - 第2次相続（Bの相続）: 承認

2. **両方の相続を放棄** ✅
   - 第1次相続（Aの相続）: 放棄
   - 第2次相続（Bの相続）: 放棄

3. **第1次相続を放棄、第2次相続を承認** ✅
   - 第1次相続（Aの相続）: 放棄
   - 第2次相続（Bの相続）: 承認

4. **第1次相続のみを承認、第2次相続を放棄** ❌ （判例により禁止）
   - 第1次相続（Aの相続）: 承認
   - 第2次相続（Bの相続）: 放棄

### 3. 実装における検証

システムでは、以下の検証を行います：

```python
def _validate_retransfer_renunciation(
    self,
    decedent: Person,                    # 第1次被相続人
    deceased_heir: Person,               # 第1次相続人（第2次被相続人）
    retransfer_targets: List[Person],    # 再転相続先（第1次相続を承認）
    second_inheritance_renounced: List[Person]  # 第2次相続の放棄者
) -> None:
    """判例制約の検証"""
    for renounced_person in second_inheritance_renounced:
        if renounced_person in retransfer_targets:
            raise RenunciationConflictError(
                f"{renounced_person.name}は{deceased_heir.name}の相続を放棄しているため、"
                f"{decedent.name}の相続のみを承認することはできません "
                f"（最高裁昭和63年6月21日判決）。"
            )
```

## テストケース

### ケース1: 判例違反（エラー）

```
A（被相続人、2025年1月死亡）
└─ B（子、2025年2月死亡、遺産分割前）
    └─ C（Bの子）

Cの選択:
- Aの相続: 承認しようとする
- Bの相続: 放棄

結果: RenunciationConflictError
```

### ケース2: 両方承認（成功）

```
A（被相続人、2025年1月死亡）
└─ B（子、2025年2月死亡、遺産分割前）
    └─ C（Bの子）

Cの選択:
- Aの相続: 承認
- Bの相続: 承認

結果: Cが全部相続 ✅
```

### ケース3: 両方放棄（成功）

```
A（被相続人、2025年1月死亡）
└─ B（子、2025年2月死亡、遺産分割前）
    └─ C（Bの子）

Cの選択:
- Aの相続: 放棄
- Bの相続: 放棄

結果: Bが相続人として残る（再転相続なし） ✅
```

### ケース4: 第1次放棄、第2次承認（成功）

```
A（被相続人、2025年1月死亡）
└─ B（子、2025年2月死亡、遺産分割前）
    └─ C（Bの子）

Cの選択:
- Aの相続: 放棄
- Bの相続: 承認

結果: Bが相続人として残る ✅
```

### ケース5: 複数の再転相続先の一部が放棄（エラー）

```
A（被相続人、2025年1月死亡）
└─ B（子、2025年2月死亡、遺産分割前）
    ├─ C（Bの子）
    └─ D（Bの子）

CとDの選択:
- C: Aの相続承認、Bの相続放棄 → エラー
- D: Aの相続承認、Bの相続承認 → OK

結果: RenunciationConflictError（Cの選択が判例違反）
```

## API使用例

### 基本的な使用方法

```python
from datetime import date
from src.models.person import Person
from src.services.inheritance_calculator import InheritanceCalculator

# 被相続人A
decedent = Person(
    name="A",
    is_decedent=True,
    is_alive=False,
    death_date=date(2025, 1, 15)
)

# 子B（遺産分割前に死亡）
child_b = Person(
    name="B",
    is_alive=False,
    death_date=date(2025, 2, 10),
    died_before_division=True  # 重要: 遺産分割前に死亡したことを示す
)

# Bの配偶者C
spouse_c = Person(name="C", is_alive=True)

# Bの子D、E
child_d = Person(name="D", is_alive=True)
child_e = Person(name="E", is_alive=True)

# 計算実行
calculator = InheritanceCalculator()

# 再転相続先の情報
retransfer_info = {
    str(child_b.id): [spouse_c, child_d, child_e]
}

# 再転相続先の関係情報
retransfer_relationships = {
    str(child_b.id): {
        str(spouse_c.id): 'spouse',
        str(child_d.id): 'child',
        str(child_e.id): 'child'
    }
}

result = calculator.calculate(
    decedent=decedent,
    spouses=[],
    children=[child_b],
    parents=[],
    siblings=[],
    retransfer_heirs_info=retransfer_info,
    retransfer_relationships=retransfer_relationships
)

# 結果
# C（配偶者）: 1/2
# D（子）    : 1/4
# E（子）    : 1/4
```

### 第2次相続放棄を含む場合

```python
# 第2次相続（Bの相続）をCが放棄
second_inheritance_renounced = {
    str(child_b.id): [child_d]  # DがBの相続を放棄
}

# DをAの相続の再転相続先から除外する必要がある
retransfer_info = {
    str(child_b.id): [spouse_c, child_e]  # Dは含まない
}

retransfer_relationships = {
    str(child_b.id): {
        str(spouse_c.id): 'spouse',
        str(child_e.id): 'child'
    }
}

result = calculator.calculate(
    decedent=decedent,
    spouses=[],
    children=[child_b],
    parents=[],
    siblings=[],
    retransfer_heirs_info=retransfer_info,
    retransfer_relationships=retransfer_relationships,
    second_inheritance_renounced=second_inheritance_renounced
)

# 結果
# C（配偶者）: 1/2 × 1/2 = 1/4
# E（子）    : 1/2 × 1/2 = 1/4
# （Dは第2次相続を放棄したため、第1次相続も承継できない）
```

### エラーハンドリング

```python
from src.utils.exceptions import RenunciationConflictError

try:
    # 判例違反のケース: DがBの相続を放棄しているのに、
    # Aの相続を承認しようとする
    retransfer_info = {
        str(child_b.id): [spouse_c, child_d, child_e]  # Dを含む
    }

    second_inheritance_renounced = {
        str(child_b.id): [child_d]  # DがBの相続を放棄
    }

    result = calculator.calculate(
        decedent=decedent,
        spouses=[],
        children=[child_b],
        parents=[],
        siblings=[],
        retransfer_heirs_info=retransfer_info,
        retransfer_relationships=retransfer_relationships,
        second_inheritance_renounced=second_inheritance_renounced
    )

except RenunciationConflictError as e:
    # エラーメッセージ:
    # "DはBの相続を放棄しているため、Aの相続のみを承認することはできません
    #  （最高裁昭和63年6月21日判決）。
    #  再転相続においては、第2次相続を放棄した者は第1次相続のみを単独で承認できません。"
    print(f"判例制約違反: {e}")
```

## 注意事項

### 1. 遺産分割前の死亡が要件

再転相続が成立するには、第1次相続人が**遺産分割前**に死亡している必要があります。遺産分割後に死亡した場合は、通常の相続（数次相続）となります。

### 2. 相続放棄の効果

相続放棄は**初めから相続人でなかったもの**とみなされます（民法939条）。したがって、第2次相続を放棄した者は、第1次相続における権利も承継できません。

### 3. 代襲相続との違い

- **再転相続**: 相続人が遺産分割前に死亡（承認・放棄をしていない）
- **代襲相続**: 相続人が被相続人より**先に**死亡（相続開始前）

## 参考文献

- 民法第896条（相続人の相続）
- 民法第900条（法定相続分）
- 民法第939条（相続放棄の効力）
- 最高裁判所判決 昭和63年6月21日（判例タイムズ680号194頁）

## 関連ファイル

- `src/services/inheritance_calculator.py` - 再転相続の計算ロジック
- `src/services/share_calculator.py` - 法定相続分の計算
- `src/utils/exceptions.py` - RenunciationConflictError定義
- `tests/test_services/test_retransfer_inheritance.py` - 再転相続の基本テスト
- `tests/test_services/test_retransfer_renunciation.py` - 判例制約のテスト

---

**最終更新日**: 2025年10月16日
**バージョン**: 1.0.0
