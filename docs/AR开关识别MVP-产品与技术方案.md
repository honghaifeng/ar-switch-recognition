# AR开关设备智能识别 — MVP产品与技术方案

> 国网青浦供电公司运检部门 | 最小可验证Demo
> 编制日期：2026年3月

---

## 一、产品定义

### 1.1 一句话描述

**运检人员戴上AR眼镜，对准任意开关设备，3秒内自动识别型号，并在视野中叠加显示铭牌信息和操作规程。**

### 1.2 MVP范围（只做这些）

| 做 | 不做（后续迭代） |
|----|----------------|
| 摄像头实时识别开关设备型号 | 远程专家协作 |
| 叠加显示铭牌信息 | 操作票AR引导 |
| 叠加显示操作规程摘要 | 语音交互 |
| 支持10种核心开关型号 | 巡检工作流 |
| 铭牌OCR自动读取 | 与PMS系统对接 |

### 1.3 MVP覆盖的10种核心开关型号

| 序号 | 型号 | 类别 | 电压等级 |
|------|------|------|---------|
| 1 | ZN63 (VS1) | 真空断路器 | 10kV |
| 2 | ZN85 | 真空断路器 | 40.5kV |
| 3 | LW36-126 | SF6断路器 | 110kV |
| 4 | GW4 | 隔离开关 | 35kV+ |
| 5 | GW5 | 隔离开关 | 35kV+ |
| 6 | KYN28 | 铠装式开关柜 | 10kV |
| 7 | XGN15 | 环网开关柜 | 10kV |
| 8 | FZN25 | 负荷开关 | 12kV |
| 9 | HXGN-12 | 箱型固定式环网柜 | 12kV |
| 10 | ZW32 | 柱上真空断路器 | 12kV |

---

## 二、用户体验流程

### 2.1 完整使用流程

```
运检人员到达变电站
      ↓
戴上 Rokid X-Craft (集成在安全帽上)
      ↓
打开"开关识别"App
      ↓
眼镜摄像头自动开启，实时取景
      ↓
对准一台开关设备（如一台开关柜）
      ↓
  ┌──────────────────────────────────────┐
  │  [识别中...]  (约1-3秒)              │
  │                                      │
  │  ┌─ 识别结果浮窗 ─────────────────┐  │
  │  │ ■ KYN28A-12 铠装式开关柜       │  │
  │  │ ─────────────────────────────  │  │
  │  │ 额定电压：12kV                 │  │
  │  │ 额定电流：630A/1250A           │  │
  │  │ 短路电流：31.5kA               │  │
  │  │ 安装位置：#3配电室 02号柜       │  │
  │  │ 投运日期：2019-06-15           │  │
  │  │ 上次检修：2025-11-20           │  │
  │  │                               │  │
  │  │ [查看操作规程]  [查看历史缺陷]  │  │
  │  └───────────────────────────────┘  │
  └──────────────────────────────────────┘
      ↓
点击 [查看操作规程]（头部动作或手势选择）
      ↓
  ┌──────────────────────────────────────┐
  │  KYN28A-12 操作规程                   │
  │  ─────────────────────────────────   │
  │  ▶ 合闸操作：                         │
  │    1. 确认小车在"试验"或"工作"位置      │
  │    2. 检查弹簧机构已储能（绿色指示）    │
  │    3. 顺时针转动合闸操作手柄            │
  │    4. 确认合闸指示灯亮（红色）          │
  │                                      │
  │  ▶ 分闸操作：                         │
  │    1. 按下分闸按钮或逆时针转动手柄      │
  │    2. 确认分闸指示灯亮（绿色）          │
  │                                      │
  │  ⚠ 安全注意事项：                      │
  │    · 操作前必须验电                    │
  │    · 小车推入/拉出时禁止合闸            │
  │    · 接地开关与断路器有机械联锁          │
  │                                      │
  │  [返回]                               │
  └──────────────────────────────────────┘
```

### 2.2 辅助识别：铭牌OCR

当AI对外观识别置信度不足时，提示用户：
```
"请对准设备铭牌，我来读取详细信息"
      ↓
摄像头对准铭牌
      ↓
OCR自动读取：型号、额定参数、出厂编号、生产厂家
      ↓
与设备知识库匹配，显示完整信息
```

---

## 三、技术架构

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Rokid X-Craft (现场端)                 │
│                                                          │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ 摄像头    │───→│ YOLOv8n      │───→│ AR Overlay    │  │
│  │ Camera2   │    │ (TFLite/INT8)│    │ (Android View)│  │
│  │ API       │    │ 设备检测+分类 │    │ 信息浮窗叠加  │  │
│  └──────────┘    └──────┬───────┘    └───────────────┘  │
│                         │                                │
│                    置信度<85%时                            │
│                         ↓                                │
│                  ┌──────────────┐                        │
│                  │ 铭牌区域裁剪  │                        │
│                  │ 发送至云端OCR │                        │
│                  └──────┬───────┘                        │
└─────────────────────────┼───────────────────────────────┘
                          │ 5G / WiFi
┌─────────────────────────┼───────────────────────────────┐
│                    云端服务 (轻量)                         │
│                         ↓                                │
│  ┌──────────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │ PaddleOCR    │  │ 设备知识库 │  │ 操作规程库          │ │
│  │ 铭牌文字识别  │  │ 10种型号  │  │ 每型号操作步骤+注意  │ │
│  │              │  │ 参数+图片  │  │ 事项+历史缺陷       │ │
│  └──────────────┘  └──────────┘  └────────────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ REST API (FastAPI)                                │   │
│  │  POST /api/ocr         — 铭牌OCR识别              │   │
│  │  GET  /api/equipment/{model} — 查询设备信息        │   │
│  │  GET  /api/procedure/{model} — 查询操作规程        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 检测模型 | YOLOv8n (Nano) | 3.2M参数，AR眼镜端可跑15-30ms/帧 |
| 模型格式 | TFLite INT8量化 | Android原生支持，NNAPI加速 |
| OCR引擎 | PaddleOCR v3 (PP-OCRv5) | 17MB，中英文混合识别，Apache开源 |
| OCR运行位置 | 云端 | 铭牌识别非实时需求，200-500ms可接受 |
| AR叠加方式 | Android Overlay Service | 原生性能最好，无需Unity |
| 后端框架 | FastAPI (Python) | 与现有光伏项目技术栈一致 |
| 设备知识库 | SQLite + JSON | MVP阶段轻量够用 |

### 3.3 为什么选混合架构（端+云）

```
                    响应速度           准确率        离线能力
端侧YOLOv8n:      ★★★★★ (30ms)     ★★★☆ (85%+)   ★★★★★
云端大模型:        ★★☆ (500ms+)      ★★★★★ (97%+)  ✗
混合方案:          ★★★★★ 主路径快     ★★★★★ 兜底准   ★★★★ 基础可用
```

- **主路径（端侧）**：YOLOv8n实时检测，3秒内给结果，无网也能用
- **辅助路径（云端）**：置信度不够时拍铭牌，OCR精准识别，查知识库返回完整信息

---

## 四、模型训练方案

### 4.1 数据集构建

**目标：10类开关设备，每类500-1000张图片**

| 数据来源 | 数量 | 说明 |
|---------|------|------|
| 现场拍摄 | 每类100-200张 | 安排运检人员在青浦各站拍摄，多角度多光线 |
| 厂家产品图 | 每类50-100张 | 从设备厂家官网、产品手册收集 |
| 网络采集 | 每类100-200张 | 百度图片、设备交易网站等 |
| 数据增强 | 扩充3-5倍 | 旋转/翻转/亮度/对比度/模糊/裁剪 |
| 合成数据 | 可选 | 利用3D模型渲染不同角度+背景 |

**标注工具：** Roboflow（在线标注+自动增强+导出YOLOv8格式）

### 4.2 训练流程

```python
# 1. 安装
# pip install ultralytics

# 2. 数据集结构
# datasets/
#   switchgear/
#     images/
#       train/    (70%)
#       val/      (15%)
#       test/     (15%)
#     labels/
#       train/
#       val/
#       test/
#     data.yaml

# 3. data.yaml 配置
# path: ./datasets/switchgear
# train: images/train
# val: images/val
# test: images/test
# names:
#   0: ZN63_VS1
#   1: ZN85
#   2: LW36_126
#   3: GW4
#   4: GW5
#   5: KYN28
#   6: XGN15
#   7: FZN25
#   8: HXGN_12
#   9: ZW32

# 4. 迁移学习训练（从COCO预训练权重开始）
from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # 加载预训练的Nano模型
results = model.train(
    data="datasets/switchgear/data.yaml",
    epochs=100,
    imgsz=640,
    batch=16,
    patience=20,        # 早停
    augment=True,       # 内置Mosaic等增强
    device=0,           # GPU
)

# 5. 评估
metrics = model.val()
print(f"mAP@0.5: {metrics.box.map50:.3f}")
print(f"mAP@0.5:0.95: {metrics.box.map:.3f}")

# 6. 导出为TFLite (INT8量化，适配AR眼镜)
model.export(format="tflite", int8=True, imgsz=320)
# 产出: best_full_integer_quant.tflite (~3-4MB)
```

### 4.3 模型性能目标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| mAP@0.5 | ≥ 90% | 10类设备识别准确率 |
| 推理延迟（端侧） | ≤ 50ms | X-Craft的NPU加速 |
| 模型大小 | ≤ 5MB | INT8量化后 |
| 误识率 | ≤ 2% | 不能把A型号识别成B |

---

## 五、软件开发方案

### 5.1 眼镜端 App（Android）

**技术栈：** Kotlin + Camera2 API + TFLite + Android Overlay

**核心模块：**

```
app/
├── camera/
│   └── CameraService.kt        # Camera2 取帧，30fps
├── detection/
│   ├── SwitchDetector.kt        # TFLite推理封装
│   └── model/
│       └── switchgear_v1.tflite # YOLOv8n INT8模型
├── ocr/
│   └── NameplateOCR.kt          # 裁剪铭牌区域，调云端OCR
├── overlay/
│   ├── AROverlayService.kt      # Android Overlay绘制浮窗
│   └── InfoCardView.kt          # 设备信息卡片UI
├── data/
│   ├── EquipmentDB.kt           # 本地设备知识库(SQLite)
│   └── ProcedureDB.kt           # 本地操作规程库
├── network/
│   └── ApiClient.kt             # 云端API调用(OCR/知识库)
└── MainActivity.kt              # 主界面，启动检测流水线
```

**核心流水线（伪代码）：**

```kotlin
// 主检测循环
class DetectionPipeline {
    fun onCameraFrame(frame: Bitmap) {
        // 1. YOLOv8推理
        val detections = switchDetector.detect(frame)

        for (det in detections) {
            if (det.confidence >= 0.85) {
                // 高置信度：直接查本地知识库
                val info = equipmentDB.query(det.className)
                overlayService.showInfoCard(det.boundingBox, info)
            } else if (det.confidence >= 0.5) {
                // 中置信度：提示对准铭牌
                overlayService.showHint("请对准设备铭牌以确认型号")
            }
            // 低置信度：忽略
        }
    }

    fun onNameplateCaptured(croppedImage: Bitmap) {
        // 发送到云端OCR
        val ocrResult = apiClient.recognizeNameplate(croppedImage)
        val info = apiClient.queryEquipment(ocrResult.modelNumber)
        overlayService.showInfoCard(info)
    }
}
```

### 5.2 云端服务（FastAPI）

```
server/
├── main.py                  # FastAPI应用入口
├── routers/
│   ├── ocr.py               # POST /api/ocr 铭牌识别
│   ├── equipment.py         # GET /api/equipment/{model}
│   └── procedure.py         # GET /api/procedure/{model}
├── services/
│   ├── ocr_service.py       # PaddleOCR封装
│   └── knowledge_service.py # 设备知识库查询
├── data/
│   ├── equipment.json       # 设备参数库
│   └── procedures.json      # 操作规程库
└── requirements.txt
```

**设备知识库示例（equipment.json）：**

```json
{
  "KYN28": {
    "full_name": "KYN28A-12 铠装移开式交流金属封闭开关设备",
    "category": "开关柜",
    "voltage": "12kV",
    "rated_current": "630A / 1250A / 1600A / 2000A / 3150A",
    "breaking_current": "31.5kA / 40kA",
    "manufacturer": "多厂家（正泰/西门子/ABB等）",
    "description": "手车式金属铠装开关柜，广泛用于10kV配电系统",
    "structure": {
      "compartments": ["母线室", "断路器手车室", "电缆室", "继电器仪表室"],
      "mechanism": "弹簧储能操作机构",
      "interlocks": ["手车位置联锁", "接地开关联锁", "柜门联锁"]
    },
    "key_points": [
      "手车有试验/工作/分离三个位置",
      "五防联锁：防误分合、防带负荷推拉、防带电挂地线、防带地线合闸、防误入带电间隔",
      "弹簧未储能时无法合闸"
    ]
  },
  "GW4": {
    "full_name": "GW4型户外交流高压隔离开关",
    "category": "隔离开关",
    "voltage": "35kV / 66kV / 110kV / 220kV",
    "rated_current": "400A-2000A",
    "type": "水平双柱旋转式",
    "description": "全国在运最广泛的高压隔离开关，约36.8万套",
    "key_points": [
      "无灭弧能力，严禁带负荷操作",
      "操作前必须确认相关断路器已分闸",
      "定期检查触头接触压力和导电回路电阻",
      "注意传动机构润滑和锈蚀问题"
    ]
  }
}
```

**操作规程示例（procedures.json）：**

```json
{
  "KYN28": {
    "inspection": {
      "title": "日常巡检要点",
      "items": [
        "检查开关柜外观有无异常变形、渗漏",
        "观察带电显示器指示是否正常",
        "检查仪表读数是否在正常范围",
        "倾听柜内有无异常放电声",
        "红外测温检查各连接点温度",
        "检查接地线连接是否可靠"
      ]
    },
    "operation": {
      "close": {
        "title": "合闸操作",
        "steps": [
          "确认手车在"试验"或"工作"位置",
          "检查弹簧储能机构已完成储能（绿色指示）",
          "核对操作票，确认操作对象无误",
          "顺时针转动合闸操作手柄至终点",
          "确认合闸到位：红色指示灯亮，电流表有指示"
        ]
      },
      "open": {
        "title": "分闸操作",
        "steps": [
          "确认操作票指令",
          "按下分闸按钮或逆时针转动操作手柄",
          "确认分闸到位：绿色指示灯亮，电流表归零",
          "如需隔离，将手车从工作位置摇至试验位置"
        ]
      }
    },
    "safety": [
      "操作前必须验电",
      "小车推入/拉出时严禁合闸",
      "接地开关与断路器有机械联锁，注意操作顺序",
      "柜内作业必须停电、验电、挂接地线、悬挂标示牌"
    ]
  }
}
```

### 5.3 API接口设计

```
POST /api/ocr
  请求: { "image": "<base64编码的铭牌图片>" }
  响应: { "texts": ["KYN28A-12", "额定电压12kV", ...], "model_number": "KYN28" }

GET /api/equipment/{model}
  示例: GET /api/equipment/KYN28
  响应: { "full_name": "...", "voltage": "12kV", ... }

GET /api/procedure/{model}?type=inspection
  示例: GET /api/procedure/KYN28?type=operation
  响应: { "operation": { "close": {...}, "open": {...} }, "safety": [...] }
```

---

## 六、硬件选型确认

### 开发阶段用 Rokid Glass 2（成本低）

| 项 | 说明 |
|----|------|
| 设备 | Rokid Glass 2 (分体式单目AR眼镜) |
| 价格 | ~1.5万/台，开发阶段买1-2台 |
| OS | YodaOS-XR (基于Android) |
| 处理器 | Amlogic S905D3 |
| 内存 | 2GB RAM |
| 摄像头 | RGB + 红外 |
| 开发方式 | Android Studio + Camera2 API + ADB调试 |
| 理由 | 轻便(96g)，成本低，SDK和社区资源多，够MVP验证 |

### 部署阶段升级 Rokid X-Craft（现场用）

| 项 | 说明 |
|----|------|
| 设备 | Rokid X-Craft (5G防爆AR头盔) |
| 价格 | ~2-3万/台 |
| 处理器 | Amlogic A311D (4GB RAM) |
| 优势 | 安全帽一体化、防爆认证、5G通信、双摄、更强算力 |
| 迁移成本 | 同为YodaOS-XR，App代码几乎不用改 |

### 开发环境

```
开发机: MacOS / Windows
IDE: Android Studio
语言: Kotlin
最低API: Android 9.0 (API 28)
调试: USB-C连接AR眼镜，adb install
```

---

## 七、项目开发计划

### 第一阶段：数据准备 + 模型训练（第1-3周）

| 周次 | 任务 | 产出 |
|------|------|------|
| W1 | 现场拍摄10种开关设备照片，每种100-200张 | 原始图片集 |
| W1 | 收集厂家产品图+网络图片 | 补充图片集 |
| W2 | Roboflow标注（画框+分类）+ 数据增强 | 标注数据集 5000+张 |
| W2 | 整理10种设备的参数+操作规程，编写JSON知识库 | equipment.json + procedures.json |
| W3 | YOLOv8n 迁移学习训练 | 训练好的模型 |
| W3 | 导出TFLite INT8，测试验证集mAP≥90% | switchgear_v1.tflite |

### 第二阶段：云端服务开发（第2-3周，与第一阶段并行）

| 周次 | 任务 | 产出 |
|------|------|------|
| W2 | 搭建FastAPI云端服务骨架 | 基础API可运行 |
| W2 | 集成PaddleOCR，实现铭牌识别接口 | POST /api/ocr |
| W3 | 实现设备查询+操作规程查询接口 | GET /api/equipment, /api/procedure |
| W3 | 部署到服务器（可复用现有47.110.154.25） | 线上可访问 |

### 第三阶段：眼镜端App开发（第3-5周）

| 周次 | 任务 | 产出 |
|------|------|------|
| W3 | Android项目搭建，Camera2取帧 | 摄像头实时预览 |
| W4 | 集成TFLite模型，实现实时检测 | 对准设备可识别型号 |
| W4 | AR Overlay浮窗，显示设备信息卡片 | 视野中叠加信息 |
| W5 | 铭牌OCR流程，云端调用 | 铭牌辅助识别可用 |
| W5 | 操作规程展示页面 | 点击可查看操作步骤 |

### 第四阶段：联调测试（第5-6周）

| 周次 | 任务 | 产出 |
|------|------|------|
| W5 | 在Rokid Glass 2上完整联调 | 端到端可用 |
| W6 | 带到青浦变电站实地测试 | 现场验证报告 |
| W6 | 收集反馈，修复问题 | MVP v1.0 |

### 总工期：约6周

---

## 八、MVP成本估算

| 项目 | 费用 | 说明 |
|------|------|------|
| Rokid Glass 2 x 2台 | 3万 | 开发+测试 |
| 云服务器 | 0 | 复用现有服务器 |
| GPU训练 | ~500元 | 阿里云GPU实例，训练几天 |
| Roboflow标注工具 | 免费版够用 | 或用LabelImg开源工具 |
| 开发人力 | 内部/外包 | 1个Android开发 + 1个后端，6周 |
| **合计硬件** | **~3.5万** | |

---

## 九、技术风险与应对

| 风险 | 概率 | 影响 | 应对方案 |
|------|------|------|---------|
| 训练数据不足，识别率不达标 | 中 | 高 | 先聚焦3-5种最常见型号；用合成数据补充；降低MVP要求至85% |
| AR眼镜算力不足，推理延迟大 | 低 | 中 | 降低输入分辨率(320x320)；减少检测频率(10fps)；改为云端推理 |
| 现场光线差，识别率下降 | 中 | 中 | 训练时加入暗光增强；利用X-Craft红外辅助；铭牌OCR兜底 |
| 设备外观相似，容易混淆 | 中 | 高 | 增加细粒度特征（铭牌区域检测）；结合安装位置辅助判断 |
| 5G/WiFi信号覆盖不全 | 低 | 低 | 端侧模型+本地知识库可离线使用，OCR为辅助功能 |

---

## 十、后续迭代路线

```
MVP (当前)                v2.0                    v3.0
识别10种开关    →    扩展到30+种设备     →    全设备覆盖
铭牌OCR辅助     →    二维码/RFID辅助      →    多模态融合
查看操作规程    →    操作票AR逐步引导     →    防误联锁集成
本地信息展示    →    远程专家实时协作     →    AI故障诊断
Glass 2开发    →    X-Craft现场部署      →    全区运检配备
```
