# Task 003: 输入来源与视频准备

## 目标

支持两种输入：

- YouTube URL
- 本地 mp4 文件

无论来源是哪一种，本任务都要把视频准备成统一的 `output/source.mp4`，并输出基础元数据 `output/source_metadata.json`。

## 本任务要做

- 在 CLI 中增加 `prepare-source` 命令。
- 判断输入是 URL 还是本地文件。
- 本地 mp4：复制到 `output/source.mp4`。
- YouTube URL：调用 `yt-dlp` 下载到 `output/source.mp4`。
- 生成 `output/source_metadata.json`。
- 给出清楚的错误提示。

## 本任务不做

- 不做音频转录。
- 不做字幕下载。
- 不做中文翻译。
- 不做叙事结构分析。
- 不做配音。
- 不做视频合成。

## 输出文件

```text
output/
  source.mp4
  source_metadata.json
```

## 验证方式

- 本地不存在的文件路径会报错。
- 本地 mp4 文件可以被复制到 `output/source.mp4`。
- YouTube URL 会尝试使用 `yt-dlp`。
- 如果没有安装 `yt-dlp`，会提示用户安装。

## 设计说明

第一版不追求复杂下载配置。先把“来源统一成 source.mp4”跑通，后续任务再基于这个文件继续做转录、翻译和分镜。

