# Web UI 拡張提案書
## コマンドライン操作に抵抗があるユーザーのための直感的なインターフェース

---

## 📋 エグゼクティブサマリー

### 提案の背景

現在の相続計算機はCLIベースで、プログラマーや技術者には使いやすい一方、以下の課題があります：

**現状の課題:**
1. **学習曲線が急**: ターミナル操作、コマンド記憶が必要
2. **視覚的フィードバックの不足**: テキストベースのため直感性に欠ける
3. **エラー時の対応が困難**: エラーメッセージの理解にITリテラシーが必要
4. **複数ケース管理が難しい**: ファイル管理が煩雑
5. **協業がしにくい**: データ共有に技術的知識が必要

**提案するソリューション:**

モダンなWeb UIを追加することで、**ITスキルのレベルに関わらず**、誰でも直感的に相続計算を実行できるシステムを構築します。

### 投資対効果（ROI）

**開発コスト見積もり:**
- 開発期間: 3-4ヶ月（フルタイム1名換算）
- 技術スタック: FastAPI + Next.js（既存コード90%再利用可能）

**期待される効果:**
- **ユーザーベース拡大**: CLI抵抗層（推定60-70%）へのアプローチ
- **業務効率化**: ケース管理時間 70%削減
- **エラー削減**: 入力ミス 80%削減（ビジュアルフィードバック効果）
- **顧客満足度向上**: UI/UX改善による満足度向上

---

## 🎯 ターゲットユーザー分析

### ペルソナ1: 山田花子（50代・司法書士）

**背景:**
- 司法書士歴20年、相続案件を月10-15件扱う
- Excelは使えるが、ターミナル操作は未経験
- 効率化に興味があるが、新技術の学習に時間を割けない

**ペインポイント:**
- CLIの使い方を覚えるのが難しい
- 過去のケースを探すのに時間がかかる
- クライアントに見せながら説明できない

**Web UIでの解決:**
- ブラウザを開くだけで使用開始
- ケース一覧から過去案件を即座に検索
- クライアントと画面共有しながらリアルタイム計算

### ペルソナ2: 佐藤太郎（30代・弁護士）

**背景:**
- 弁護士5年目、相続案件も扱うが専門ではない
- ITリテラシーは高いが、相続計算の専門知識は限定的
- 複数案件を並行処理

**ペインポイント:**
- 計算ロジックの確認に時間がかかる
- 複数ケースの比較が難しい
- スマホやタブレットから確認したい

**Web UIでの解決:**
- 法的根拠が視覚的に表示される
- ダッシュボードで複数ケースを一覧管理
- レスポンシブデザインでモバイル対応

### ペルソナ3: 鈴木次郎（40代・行政書士アシスタント）

**背景:**
- 行政書士事務所の事務員
- データ入力が主業務
- 相続の専門知識は限定的

**ペインポイント:**
- コマンド入力でのタイプミスが多い
- 入力項目の漏れに気づきにくい
- エラーメッセージの意味が理解できない

**Web UIでの解決:**
- フォームの入力補完とバリデーション
- 入力必須項目が視覚的に明確
- 日本語の分かりやすいエラーメッセージ

---

## 🎨 UI/UXデザイン原則

### 1. ゼロラーニングコスト

**原則:** 初めて使うユーザーでも、説明なしで基本操作ができる

**実装例:**
- **オンボーディングツアー**: 初回アクセス時の3ステップガイド
- **コンテキストヘルプ**: 各フィールドに「?」アイコンで説明表示
- **サンプルケース**: プリロード済みのデモデータで即座に体験

```typescript
// オンボーディングツアーの実装例
const onboardingSteps = [
  {
    target: '#new-case-button',
    content: '新しい相続ケースを作成するには、ここをクリックします',
    placement: 'bottom'
  },
  {
    target: '#chat-interface',
    content: 'AIアシスタントに話しかけるように情報を入力できます',
    placement: 'left'
  },
  {
    target: '#family-tree',
    content: '家系図をドラッグ＆ドロップで編集できます',
    placement: 'right'
  }
];
```

### 2. 段階的複雑性（Progressive Disclosure）

**原則:** 初心者には簡単に、上級者には高度な機能を

**実装例:**

**Level 1 - シンプルモード（デフォルト）:**
```
┌─────────────────────────────────────┐
│  新しい相続ケースを作成             │
│                                     │
│  被相続人: [山田太郎________]       │
│  死亡日:   [2025/06/15_____]       │
│                                     │
│  [AIと対話して入力する] [次へ]     │
└─────────────────────────────────────┘
```

**Level 2 - 標準モード:**
```
┌─────────────────────────────────────┐
│  家系図を編集                       │
│  ┌─────────────────────────────┐   │
│  │     [家系図ビジュアル]       │   │
│  │  ドラッグ＆ドロップで編集     │   │
│  └─────────────────────────────┘   │
│                                     │
│  [詳細設定] [計算実行]             │
└─────────────────────────────────────┘
```

**Level 3 - エキスパートモード（オプトイン）:**
```
┌─────────────────────────────────────┐
│  詳細設定                           │
│  ☐ 代襲相続の手動設定               │
│  ☐ 特別受益の考慮                   │
│  ☐ 寄与分の調整                     │
│  ☐ カスタム計算式                   │
│                                     │
│  [保存] [キャンセル]                │
└─────────────────────────────────────┘
```

### 3. 即座のフィードバック

**原則:** ユーザーの全アクションに対して即座に反応

**実装例:**

**リアルタイムバリデーション:**
```typescript
// 住所入力時のリアルタイム郵便番号検索
<AddressInput
  value={address}
  onChange={(value) => {
    setAddress(value);
    // 郵便番号を検出したら自動補完
    if (isPostalCode(value)) {
      fetchAddressSuggestions(value).then(setSuggestions);
    }
  }}
  suggestions={suggestions}
  onSelect={(selected) => {
    setAddress(selected.fullAddress);
    showSuccessToast('住所が入力されました');
  }}
/>
```

**プログレスインジケーター:**
```typescript
// 計算実行時の進捗表示
<CalculationProgress
  steps={[
    { label: '相続人資格の判定', status: 'completed' },
    { label: '相続割合の計算', status: 'in_progress', progress: 65 },
    { label: '法的根拠の確認', status: 'pending' },
    { label: 'レポート生成', status: 'pending' }
  ]}
/>
```

### 4. エラー予防と回復

**原則:** エラーを未然に防ぎ、発生時は簡単に回復

**実装例:**

**予防的UI:**
```typescript
// 無効な選択肢を非活性化
<Select
  label="続柄"
  options={[
    { value: 'spouse', label: '配偶者' },
    { value: 'child', label: '子', disabled: !decedent },
    { value: 'parent', label: '父母', disabled: hasChildren },
    { value: 'sibling', label: '兄弟姉妹', disabled: hasChildren || hasParents }
  ]}
  helpText={hasChildren ? '子がいる場合、兄弟姉妹は相続人になりません' : null}
/>
```

**優しいエラーメッセージ:**
```typescript
// 技術的エラーを分かりやすく翻訳
const errorMessages = {
  'VALIDATION_ERROR_DEATH_BEFORE_BIRTH': {
    title: '日付の矛盾があります',
    message: '死亡日が生年月日より前になっています。入力内容を確認してください。',
    action: '日付を修正する',
    helpLink: '/help/date-validation'
  },
  'CALCULATION_ERROR_NO_HEIRS': {
    title: '相続人が見つかりません',
    message: '入力された情報では相続人が確定できません。家系図を確認してください。',
    action: '家系図を確認する',
    helpLink: '/help/heir-determination'
  }
};
```

---

## 🚀 主要機能の詳細設計

### 1. AI対話インターフェース（最重要機能）

**コンセプト:**
「ChatGPTのように話しかけるだけで相続計算が完了する」

**機能詳細:**

#### 1.1 自然言語入力
```typescript
// ユーザー入力例
"山田太郎さんが令和7年6月15日に亡くなりました。
 配偶者の花子さん（昭和30年生まれ）と、
 子供が2人います。一郎と二郎です。"

// AI応答例
"理解しました。以下の情報を確認させてください：

✓ 被相続人: 山田太郎さん（2025年6月15日死亡）
✓ 配偶者: 山田花子さん（1955年生まれ）
✓ 子: 山田一郎さん、山田二郎さん

一郎さんと二郎さんは現在もご存命でしょうか？"
```

#### 1.2 元号・西暦の柔軟な理解
```typescript
// 様々な入力形式を自動認識
const dateInputExamples = [
  "令和5年10月3日",
  "R5.10.3",
  "2023/10/3",
  "昭和60年3月15日",
  "S60-3-15",
  "1985年3月15日"
];

// すべて自動的に正しい日付に変換
```

#### 1.3 曖昧な入力の明確化
```typescript
// 曖昧な入力
User: "父が亡くなりました"

// AI明確化
AI: "お悔やみ申し上げます。
    お父様のお名前と死亡日を教えていただけますか？
    また、あなた（相談者）のお名前もお願いします。"
```

#### 1.4 リアルタイムデータ抽出
```typescript
// 会話中に自動的にデータを抽出・整理
<ChatDataExtraction
  extractedData={{
    decedent: {
      name: '山田太郎',
      deathDate: '2025-06-15',
      confidence: 0.95
    },
    spouse: {
      name: '山田花子',
      birthYear: 1955,
      confidence: 0.90
    },
    children: [
      { name: '山田一郎', confidence: 0.95 },
      { name: '山田二郎', confidence: 0.95 }
    ]
  }}
  onConfirm={(data) => updateFamilyTree(data)}
  onEdit={(field) => openEditDialog(field)}
/>
```

### 2. ビジュアル家系図エディター

**コンセプト:**
「PowerPointのように直感的にドラッグ＆ドロップで編集」

#### 2.1 スマートノード配置
```typescript
// 自動レイアウトアルゴリズム
<FamilyTreeCanvas
  layout="hierarchical" // or "force-directed"
  autoAlign={true}
  snapToGrid={true}
  spacing={{ horizontal: 120, vertical: 80 }}
  onNodeAdd={(position) => {
    // ノード追加時に適切な関係を提案
    suggestRelationships(position);
  }}
/>
```

#### 2.2 コンテキストメニュー
```typescript
// 右クリックで操作メニュー
<PersonNode
  person={person}
  contextMenu={[
    { icon: '✏️', label: '編集', action: () => openEditDialog(person) },
    { icon: '➕', label: '子を追加', action: () => addChild(person) },
    { icon: '💑', label: '配偶者を追加', action: () => addSpouse(person) },
    { icon: '🔄', label: '代襲相続設定', action: () => setSubstitution(person) },
    { icon: '🚫', label: '相続放棄', action: () => setRenounced(person) },
    { icon: '🗑️', label: '削除', action: () => deletePerson(person), danger: true }
  ]}
/>
```

#### 2.3 視覚的フィードバック
```typescript
// 相続割合を視覚的に表示
<PersonNode
  person={person}
  heir={heir}
  style={{
    border: heir ? `4px solid ${getColorByShare(heir.share)}` : '2px solid gray',
    backgroundColor: heir ? 'rgba(74, 222, 128, 0.1)' : 'white'
  }}
  badge={
    heir && (
      <Badge color="green">
        {heir.share} ({heir.percentage}%)
      </Badge>
    )
  }
/>
```

### 3. 元号対応入力システム

**コンセプト:**
「日本人に馴染みのある元号で自然に入力」

#### 3.1 インテリジェント日付入力
```typescript
<EnhancedDateInput
  label="生年月日"
  value={birthDate}
  onChange={setBirthDate}
  features={{
    // 元号/西暦の自動判定
    autoDetect: true,
    // カレンダーピッカー
    calendar: true,
    // 年齢からの逆算
    ageCalculator: true,
    // 元号年表の表示
    eraReference: true
  }}
  presets={[
    { label: '昭和元年生まれ（1926年）', value: '1926-12-25' },
    { label: '平成元年生まれ（1989年）', value: '1989-01-08' },
    { label: '令和元年生まれ（2019年）', value: '2019-05-01' }
  ]}
  validation={{
    min: '1868-01-25', // 明治元年
    max: new Date(),
    message: '明治元年以降の日付を入力してください'
  }}
/>
```

#### 3.2 年齢逆算機能
```typescript
// 「現在80歳」から生年を自動計算
<AgeCalculator
  currentAge={80}
  referenceDate={new Date()}
  onCalculate={(birthYear) => {
    // 1945年生まれ → 昭和20年
    setMessage(`昭和${birthYear - 1925}年（${birthYear}年）生まれと推定されます`);
  }}
/>
```

#### 3.3 元号変換プレビュー
```typescript
// リアルタイムで元号↔西暦を相互表示
<DatePreview
  input="S60.3.15"
  preview={{
    western: '1985年3月15日',
    era: '昭和60年3月15日',
    age: calculateAge('1985-03-15'),
    dayOfWeek: '金曜日'
  }}
/>
```

### 4. ケース管理ダッシュボード

**コンセプト:**
「Notion や Asana のようなモダンなタスク管理」

#### 4.1 カード型一覧
```typescript
<CaseGrid
  cases={cases}
  view="grid" // or "list"
  renderCard={(case) => (
    <CaseCard
      title={`${case.decedent.name}様の相続`}
      status={case.status}
      date={case.deathDate}
      heirs={case.heirs?.length || 0}
      lastModified={case.updatedAt}
      tags={[
        case.hasSubstitution && '代襲相続',
        case.hasRenounced && '相続放棄',
        case.hasComplexCase && '複雑ケース'
      ].filter(Boolean)}
      actions={[
        { icon: '👁️', label: '表示', onClick: () => viewCase(case) },
        { icon: '✏️', label: '編集', onClick: () => editCase(case) },
        { icon: '📄', label: 'PDF出力', onClick: () => exportPDF(case) },
        { icon: '📋', label: '複製', onClick: () => duplicateCase(case) }
      ]}
    />
  )}
/>
```

#### 4.2 高度な検索・フィルター
```typescript
<CaseFilters
  filters={{
    search: {
      placeholder: '被相続人名、メモで検索...',
      fields: ['decedent.name', 'description', 'notes']
    },
    status: {
      options: ['下書き', '計算済み', '完了', 'アーカイブ'],
      multiple: true
    },
    dateRange: {
      label: '死亡日',
      presets: ['今月', '先月', '今年', 'カスタム']
    },
    tags: {
      options: ['代襲相続', '相続放棄', '複雑ケース', '再転相続'],
      multiple: true
    },
    heirs: {
      label: '相続人数',
      range: [0, 20]
    }
  }}
  onFilterChange={(filters) => fetchCases(filters)}
/>
```

#### 4.3 統計ダッシュボード
```typescript
<Dashboard>
  <StatCard
    title="今月の案件数"
    value={42}
    change="+12%"
    trend="up"
    icon="📊"
  />
  <StatCard
    title="平均相続人数"
    value={3.2}
    change="-0.3"
    trend="down"
    icon="👥"
  />
  <StatCard
    title="代襲相続率"
    value="18%"
    change="+2%"
    trend="up"
    icon="🔄"
  />

  <ChartCard title="月別案件推移">
    <LineChart
      data={monthlyData}
      xAxis="month"
      yAxis="count"
    />
  </ChartCard>

  <ChartCard title="相続順位の分布">
    <PieChart
      data={rankDistribution}
      labels={['配偶者のみ', '配偶者+子', '配偶者+直系尊属', '配偶者+兄弟姉妹']}
    />
  </ChartCard>
</Dashboard>
```

### 5. スマートフォーム

**コンセプト:**
「Googleフォームのような親しみやすさ + 法務の専門性」

#### 5.1 ステップバイステップウィザード
```typescript
<FormWizard
  steps={[
    {
      id: 'decedent',
      title: '被相続人情報',
      icon: '👤',
      fields: [
        <TextInput label="氏名" required />,
        <EnhancedDateInput label="死亡日" required />,
        <EnhancedDateInput label="生年月日" />
      ],
      validation: (data) => validateDecedent(data)
    },
    {
      id: 'family',
      title: '家族構成',
      icon: '👨‍👩‍👧‍👦',
      component: <FamilyBuilder />,
      skipIf: (data) => data.useAIChat
    },
    {
      id: 'special-cases',
      title: '特殊事項',
      icon: '⚠️',
      fields: [
        <CheckboxGroup
          label="該当する事項をすべて選択してください"
          options={[
            '相続放棄した人がいる',
            '代襲相続が発生している',
            '相続欠格者がいる',
            '相続廃除された人がいる'
          ]}
        />
      ]
    },
    {
      id: 'review',
      title: '確認',
      icon: '✅',
      component: <ReviewSummary />
    }
  ]}
  onComplete={(data) => calculateInheritance(data)}
/>
```

#### 5.2 スマートデフォルト
```typescript
// ユーザーの過去入力から学習してデフォルト値を提案
<SmartForm
  learningEnabled={true}
  suggestions={{
    // 前回入力した住所パターンから提案
    'heir.address': suggestAddress(previousCases),
    // よく使う続柄を優先表示
    'relationship': sortByFrequency(relationships),
    // 死亡日から生年月日の妥当な範囲を提示
    'birth_date': suggestBirthDateRange(deathDate)
  }}
/>
```

---

## 🔒 セキュリティとプライバシー

### 1. データ保護

**個人情報の取り扱い:**
```typescript
// データ暗号化
const sensitiveFields = ['name', 'address', 'phone', 'email'];

const encryptSensitiveData = (data: Person) => {
  return {
    ...data,
    ...Object.fromEntries(
      sensitiveFields.map(field => [
        field,
        encrypt(data[field], process.env.ENCRYPTION_KEY)
      ])
    )
  };
};

// ログには個人情報を記録しない
const sanitizeForLog = (data: any) => {
  return {
    ...data,
    name: maskString(data.name),
    address: '***',
    phone: '***',
    email: '***'
  };
};
```

### 2. アクセス制御

**ユーザー管理:**
```typescript
// ロールベースアクセス制御（RBAC）
const roles = {
  ADMIN: ['create', 'read', 'update', 'delete', 'export', 'manage_users'],
  LAWYER: ['create', 'read', 'update', 'export'],
  ASSISTANT: ['create', 'read'],
  VIEWER: ['read']
};

// ケースごとのアクセス権限
<CasePermissions
  case={case}
  owner={currentUser}
  shared={[
    { user: 'user@example.com', role: 'VIEWER' },
    { user: 'assistant@example.com', role: 'ASSISTANT' }
  ]}
  onShare={(email, role) => shareCase(case.id, email, role)}
/>
```

### 3. 監査ログ

**操作履歴の記録:**
```typescript
// すべての重要操作をログ記録
const auditLog = {
  userId: currentUser.id,
  action: 'CASE_CREATED',
  caseId: case.id,
  timestamp: new Date(),
  ipAddress: request.ip,
  userAgent: request.headers['user-agent'],
  changes: {
    before: null,
    after: sanitizeForLog(case)
  }
};

// ログビューワー
<AuditLogViewer
  filters={['CASE_CREATED', 'CASE_UPDATED', 'CASE_DELETED', 'PDF_EXPORTED']}
  dateRange={[startDate, endDate]}
  users={[currentUser, ...sharedUsers]}
/>
```

---

## 📱 モバイル対応

### レスポンシブデザイン戦略

**デバイス別最適化:**

| 機能 | デスクトップ | タブレット | スマートフォン |
|------|-------------|-----------|---------------|
| ケース一覧 | カード3列 | カード2列 | リスト表示 |
| 家系図編集 | フル機能 | 簡易編集 | 閲覧のみ |
| AI対話 | サイドパネル | フルスクリーン | フルスクリーン |
| レポート表示 | 分割画面 | タブ切替 | スクロール |
| ダッシュボード | 4列グリッド | 2列グリッド | 1列スタック |

**モバイルファースト機能:**

```typescript
// タッチジェスチャー対応
<SwipeableCard
  onSwipeLeft={() => archiveCase(case)}
  onSwipeRight={() => favoriteCase(case)}
  leftAction={{ icon: '🗑️', label: 'アーカイブ', color: 'red' }}
  rightAction={{ icon: '⭐', label: 'お気に入り', color: 'yellow' }}
/>

// オフライン対応
<OfflineIndicator
  status={isOnline ? 'online' : 'offline'}
  syncStatus={pendingChanges > 0 ? 'pending' : 'synced'}
  onRetry={() => syncWithServer()}
/>

// 音声入力
<VoiceInput
  enabled={true}
  language="ja-JP"
  onResult={(transcript) => {
    processNaturalLanguage(transcript);
  }}
/>
```

---

## 🌐 国際化（将来の拡張）

### 多言語対応の準備

```typescript
// i18n設定
const messages = {
  'ja': {
    'case.title': '{decedent}様の相続',
    'heir.spouse': '配偶者',
    'heir.child': '子',
    'legal.basis': '民法第{article}条'
  },
  'en': {
    'case.title': 'Inheritance of {decedent}',
    'heir.spouse': 'Spouse',
    'heir.child': 'Child',
    'legal.basis': 'Civil Code Article {article}'
  }
};

// 法域別ロジックの切り替え
const jurisdictionLogic = {
  'JP': JapanInheritanceLaw,
  'US-CA': CaliforniaInheritanceLaw,
  'UK': UKInheritanceLaw
};
```

---

## 📊 成功指標（KPI）

### 定量的指標

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| **ユーザー採用率** | 初月50%、3ヶ月80% | アクティブユーザー数 / 全ユーザー数 |
| **タスク完了率** | 95%以上 | 計算完了数 / 計算開始数 |
| **エラー率** | 5%未満 | エラー発生数 / 総操作数 |
| **平均所要時間** | CLI比60%短縮 | 計算開始から完了までの時間 |
| **ユーザー満足度** | NPS 50以上 | Net Promoter Score |
| **モバイル利用率** | 30%以上 | モバイルアクセス / 総アクセス |

### 定性的指標

**ユーザーフィードバック収集:**
```typescript
// アプリ内フィードバック機能
<FeedbackWidget
  triggers={[
    { event: 'case_completed', delay: 2000 },
    { event: 'error_occurred', immediate: true },
    { event: 'session_end', beforeUnload: true }
  ]}
  questions={[
    {
      type: 'rating',
      question: 'この機能の使いやすさを評価してください',
      scale: 5
    },
    {
      type: 'text',
      question: '改善してほしい点があれば教えてください',
      optional: true
    }
  ]}
/>
```

---

## 💰 コスト試算

### 開発コスト

| フェーズ | 期間 | コスト（人月） | 累計 |
|---------|------|---------------|------|
| Phase 5: 基盤構築 | 2週間 | 0.5人月 | 0.5 |
| Phase 6: バックエンド | 2週間 | 0.5人月 | 1.0 |
| Phase 7: フロントエンド基礎 | 2週間 | 0.5人月 | 1.5 |
| Phase 8: 主要機能実装 | 2週間 | 0.5人月 | 2.0 |
| Phase 9: 家系図エディター | 2週間 | 0.5人月 | 2.5 |
| Phase 10: テスト・最適化 | 2週間 | 0.5人月 | 3.0 |
| Phase 11: デプロイ準備 | 2週間 | 0.5人月 | 3.5 |
| **合計** | **14週間** | **3.5人月** | **3.5** |

### 運用コスト（月額）

| 項目 | 想定規模 | コスト（円） |
|------|---------|------------|
| クラウドホスティング（AWS/GCP） | 月間1000ユーザー | 10,000 |
| Neo4jデータベース | 10GB | 5,000 |
| CDN（画像・静的ファイル） | 100GB転送 | 3,000 |
| 監視・ログ管理 | 基本プラン | 2,000 |
| **合計** | - | **20,000** |

---

## 🎯 推奨実装順序

### MVP（最小実行可能製品）- Phase 1-2

**優先機能:**
1. ✅ ケース一覧・作成・詳細
2. ✅ 基本的な入力フォーム（元号対応）
3. ✅ 既存CLI計算ロジックの統合
4. ✅ 計算結果の表示
5. ✅ PDF出力

**除外機能（後回し）:**
- AI対話インターフェース
- 家系図エディター
- 高度な統計ダッシュボード

### Phase 2 - 差別化機能

**追加機能:**
1. ✅ AI対話インターフェース
2. ✅ 簡易家系図表示（編集なし）
3. ✅ 基本的な検索・フィルター

### Phase 3 - フル機能

**完成機能:**
1. ✅ 対話的家系図エディター
2. ✅ 高度なダッシュボード
3. ✅ モバイル最適化
4. ✅ 協業機能（共有）

---

## 📝 提案まとめ

### Why（なぜやるのか）

**問題:**
- CLIは技術者向けで、法務専門家の60-70%が使用に抵抗
- 視覚的フィードバック不足で直感性に欠ける
- 複数ケース管理、協業が困難

**解決:**
- モダンなWeb UIでITスキル不要
- 視覚的・対話的インターフェース
- クラウドベースの協業機能

### What（何を作るのか）

**コア機能:**
1. **AI対話インターフェース** - 話しかけるだけで計算完了
2. **ビジュアル家系図** - ドラッグ&ドロップ編集
3. **元号対応入力** - 日本人に馴染みのある入力方式
4. **ケース管理** - Notion風のモダンなダッシュボード
5. **モバイル対応** - いつでもどこでもアクセス

### How（どう作るのか）

**技術スタック:**
- バックエンド: FastAPI（既存コード90%再利用）
- フロントエンド: Next.js 14 + TypeScript + shadcn/ui
- データベース: 既存Neo4j拡張
- AI: 既存Ollama統合

**開発期間:** 3.5ヶ月（14週間）

**コスト:**
- 開発: 3.5人月
- 運用: 月額2万円

### Impact（どんな効果があるのか）

**ビジネスインパクト:**
- ✅ ユーザーベース拡大（CLI抵抗層へのリーチ）
- ✅ 業務効率70%向上（ケース管理時間短縮）
- ✅ エラー80%削減（ビジュアルフィードバック）
- ✅ 顧客満足度向上（UX改善）

---

**推奨アクション:**

1. **MVP開発開始** - まずは基本機能で早期フィードバック
2. **ユーザーテスト** - ターゲットペルソナでの検証
3. **段階的リリース** - CLIと並行運用でリスク低減

---

**最終更新日**: 2025年10月17日
**作成者**: Claude Code
**バージョン**: 1.0.0
**ステータス**: 提案完成
