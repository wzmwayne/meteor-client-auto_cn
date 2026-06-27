# AGENTS.md - Meteor Client

## Build & Run

```bash
./gradlew build                          # 构建 mod JAR
./gradlew build -Pbuild_number=123       # 指定构建号（CI 会用）
./gradlew publish                        # 发布到 Meteor Maven（需凭据）
```

- JDK 25（temurin），Gradle 配置了缓存和并行编译
- 构建产物在 `build/libs/`

## 项目结构

- `src/main/` — 主 mod 代码，入口 `meteordevelopment.meteorclient.MeteorClient`（`ClientModInitializer`）
- `src/launcher/` — 独立启动器（Java 8 兼容），入口 `Main.java`，编译到 JAR 的 `Main-Class`
- 单模块 Fabric Loom 项目，使用 access widener (`meteor-client.classtweaker`)

## Mixin 系统

- `MixinPlugin` 根据加载的模组条件启用混入：
  - `mixin/sodium/` → Sodium，`mixin/indigo/` → Indigo，`mixin/lithium/` → Lithium，`mixin/viafabricplus/` → ViaFabricPlus
  - `PlayerEntityRendererMixin` 在 Origins 存在时跳过
- 兼容性混入配置分散在多个 `meteor-client-*.mixins.json` 中，都在 `fabric.mod.json` 注册

## 初始化机制

自定义 `@PreInit` / `@PostInit` 注解驱动，通过 `ReflectInit` 扫描 `@MeteorAddon#getPackage()` 路径下的注解方法，支持 `dependencies` 排序。
`registerPackages()` → `init(PreInit.class)` → `init(PostInit.class)`。

## 关键库

- **Orbit** — 事件总线（`meteordevelopment.orbit.IEventBus`）
- **Starscript** — 脚本引擎
- JAR-in-JAR 引用：Reflections、Discord IPC、Netty handler proxy/codec socks、WaybackAuthLib
- **compileOnly**：Sodium、Lithium、Iris、ViaFabricPlus、Baritone、ModMenu

## 代码规范

- Google Java Style Guide
- 所有 Java 文件必须带 GPL-3.0 license header（见已有文件顶部）
- 4 空格缩进（Java），2 空格缩进（JSON/YAML），UTF-8
- 编译警告：`-Xlint:deprecation`、`-Xlint:unchecked`
- Favour readability over compactness
- 所有 Java 源文件必须含版权头

## CI (GitHub Actions)

- PR：`./gradlew build` → 上传 `build/libs/` 作为 artifact
- master push：`build`（含 build_number、commit 参数）→ `publish`
- JDK 25 + Node 24

## 注意事项

- 无测试框架
- 版本格式：`{minecraft版本}-{build号}`，local 构建后缀为 `local`
- 数据文件夹：`<游戏目录>/meteor-client/`
- Fabric API 仅引入 `fabric-api-base` 和 `fabric-resource-loader-v1`
