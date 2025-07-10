# OpenLoong Dora集成项目开发日志

## 6月15日至6月30日
### 项目开发准备阶段工作摘要
 - 搭建dora环境
 - 运行Dora样例熟悉Dora数据流
 - 搭建Openloong全身动力学系统仿真环境
 - 运行Openloong全身动力学仿真实例
 - 搭建gRPC环境, 在macOS,Ubuntu20.04尝试从源码构建gRPC
 - 使用发行版gRPC构建GPS导航接口, 根据proto提供的service函数接口构建了server/client导航样例
 - 使用发行版gRPC构建机器人上肢控制接口, 根据proto提供的service函数接口构建了server/client上肢控制样例

### 开发过程记录
#### 6月25日: 在Ubuntu20.04环境中使用CMake从源码编译gRPC
 - 从仓库拉取源码过程中需要递归拉取子模块,容易因为网络连接不稳定导致拉取失败; 根据gRPC的C++ tutrial构建helloWorld样例时, CMakeLists无法在找到cmake目录下找到common.cmake文件

#### 7月5日: 在macOS环境中使用bzael从源码编译gRPC
 - 第一次使用bazel编译, 不熟悉编译流程, 在根据gRPC tutorial进行到:
    ```
    # Run all the C/C++ tests
    $ bazel test --config=dbg //test/...
    ```
    出现:
    ```
    Executed 486 out of 1933 tests: 400 tests pass, 1 fails to build, 86 fail locally, and 1446 were skipped.
    There were tests whose specified size is too big. Use the --test_verbose_timeout_warnings command line option to see which ones these are.
    ```
    推测是因为拉取子模块超时导致的失败;
#### 7月6日: 在macOS环境中使用发行版gRPC构建样例: 使用Dora封装client工作流

#### 7月9日: 在使用dataflow.yml构建工作流时遇到
```
    (openloong-dora) ➜  openloong-dora-workflow git:(openloong-dora) ✗ dora run test_data.yml --uv


    [ERROR]
    failed to parse given descriptor

    Caused by:
        nodes[1].inputs: data did not match any variant of untagged enum InputDef at line 12 column 7

    Location:
        libraries/core/src/descriptor/mod.rs:129:38
```