# Windows 构建指南

本文档介绍如何在 Windows 上构建微信公众号文章总结器的可执行文件和安装程序。

## 前置要求

### 必需软件

1. **Python 3.10+**
   - 下载: https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. **Git**
   - 下载: https://git-scm.com/download/win

3. **Inno Setup 6** (可选，用于创建安装程序)
   - 下载: https://jrsoftware.org/isdl.php
   - 安装后将 ISCC.exe 添加到 PATH

### 验证安装

```powershell
python --version  # 应显示 Python 3.10+
git --version
iscc /version     # 可选
```

## 快速构建

### 使用构建脚本

```powershell
# 克隆项目
git clone https://github.com/your-username/wechat-article-summarizer.git
cd wechat-article-summarizer

# 运行构建脚本
.\build\build_windows.ps1
```

构建完成后，输出文件在：
- `dist/wechat-summarizer.exe` - 可执行文件
- `output/WechatSummarizer-x.x.x-Setup.exe` - 安装程序
- `dist/checksums.sha256` - SHA256 校验和

### 跳过测试

```powershell
.\build\build_windows.ps1 -SkipTests
```

### 跳过安装程序

```powershell
.\build\build_windows.ps1 -SkipInstaller
```

## 手动构建

### 1. 设置虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```powershell
pip install -e .[full,build]
```

### 3. 运行测试

```powershell
pytest tests/ -v
```

### 4. PyInstaller 打包

```powershell
pyinstaller build/pyinstaller.spec --clean
```

### 5. 创建安装程序

```powershell
iscc build/installer.iss
```

## 自定义构建

### 添加应用图标

1. 准备 ICO 文件（多分辨率：16x16, 32x32, 48x48, 64x64, 128x128, 256x256）
2. 放置到 `assets/icons/app.ico`
3. 重新运行 PyInstaller

### 修改版本号

编辑以下文件：
- `pyproject.toml` - `version = "x.x.x"`
- `build/installer.iss` - `#define MyAppVersion "x.x.x"`
- `src/wechat_summarizer/shared/constants.py` - `VERSION = "x.x.x"`

### 添加数据文件

编辑 `build/pyinstaller.spec`：

```python
datas=[
    ('README.md', '.'),
    ('LICENSE', '.'),
    ('path/to/data', 'destination'),  # 添加新文件
],
```

## 代码签名

### 获取代码签名证书

1. 从受信任的 CA 购买代码签名证书
2. 或使用自签名证书（仅用于测试）

### 签名可执行文件

```powershell
# 使用 signtool（Windows SDK 的一部分）
signtool sign /f your-cert.pfx /p password /t http://timestamp.digicert.com dist/wechat-summarizer.exe
```

### 签名安装程序

在 `installer.iss` 中添加：

```ini
[Setup]
SignTool=signtool sign /f $qcert.pfx$q /p $qpassword$q /t http://timestamp.digicert.com $f
```

## 故障排除

### PyInstaller 找不到模块

确保所有隐藏导入都已添加到 spec 文件：

```python
hiddenimports = [
    'wechat_summarizer.module_name',
    # 添加缺失的模块
]
```

### 安装程序创建失败

1. 检查 Inno Setup 是否正确安装
2. 检查 `installer.iss` 中的路径是否正确
3. 确保 `dist/wechat-summarizer.exe` 存在

### 运行时错误

1. 检查是否缺少 DLL 文件
2. 使用 Dependency Walker 分析依赖
3. 尝试在干净的 Windows 虚拟机上测试

## CI/CD 集成

项目已配置 GitHub Actions 自动构建，见 `.github/workflows/build.yml`。

### 触发条件

- Push 到 `main` 分支
- 创建 Release

### 构建产物

- Windows 可执行文件
- Windows 安装程序
- Python wheel 包

## 发布清单

发布前检查：

- [ ] 更新版本号
- [ ] 更新 CHANGELOG.md
- [ ] 所有测试通过
- [ ] 在干净环境测试可执行文件
- [ ] 在干净环境测试安装程序
- [ ] 代码签名（如适用）
- [ ] 生成 SHA256 校验和
- [ ] 创建 GitHub Release
