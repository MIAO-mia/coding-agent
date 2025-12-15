Environment requirement: python==3.10, the latest openai, packaging, psutil
ATTENTION: CREATE A NEW ENVIRONMENT TO USE THIS CODING AGENT! BECAUSE IT WILL DIRECTLY INSTALL NEW PACKAGES IN THE CURRENT ENVIRONMENT!
环境要求：python==3.10，最新的openai, packaging, psutil。
注意：请务必新建一个环境来运行这个代码，因为这个Coding Agent会直接将需要的包安装在当前环境。

HOW TO USE
使用指南

1. In config.py, point where you want the project to generate.
1. 在config.py里，请指定好你想让项目生成的文件夹。

2. run main.py
2. 运行main.py

3. Choose mode. Mode 1 is generating a project from nothing, you only need to input your demand. Mode 2 is modify existing project, you need to input your demand and the path of the project. We use deepseek v3.2 reasoner, and it output the whole code in one go, so you may wait a long time for generation.
3. 你需要先选择模式。Mode 1是直接使用提示词从零生成新项目，你只要输入你的需求就可以了。Mode 2是修改已有项目，你需要输入你的需求和项目所在的文件夹路径。我们使用的模型是深度求索v3.2的思考模式，而且是一次性生成完整代码，所以生成会要比较久。

4. To input your demand, input in one line. Use \n as line break.
4. 输入需求需要把所有内容放在一行。用\n来作为换行符。
Build an "arXiv CS Daily" webpage with three core functionalities to deliver a streamlined experience for tracking daily computer science preprints:\n1. Domain-Specific Navigation System\nImplement categorized navigation based on arXiv's primary CS fields (cs.AI, cs.TH, cs.SY, etc.). This enables users to quickly filter and switch between major subfields, ensuring easy access to their areas of interest.\n2. Daily Updated Paper List\nCreate a daily updated list displaying the latest papers with essential details only. Each entry may include the paper title (hyperlinked to its detail page), submission time, and the specificarXiv field tag (e.g., [cs.CV]).\n3. Dedicated Paper Detail Page\nDesign a comprehensive detail page that centralizes critical resources: direct PDF link (hosted on arXiv), core metadata (title, authors with affiliations, submission date), and citation generationtools supporting common formats (BibTeX, standard academic citation) with one-click copy functionality.

5. After the first generation, the program will run the code itself. If error occurs, it will report to the LLM aotomatically for fixing. If successfully run, you need Ctrl+C to stop web server, then we'll enter the next phase.
5. 生成代码之后，程序会自动运行写好的代码。如果有报错，会自动将错误返回给大模型修改。如果成功运行了，你需要Ctrl+C来停止网页服务器的运行，只有这样才能进入下一个部分。

6. Now, you can input exit to exit the program, or input more demand to let LLM make modifications.
6. 现在，你可以输入exit来退出程序，或者输入更多需求让大模型继续修改代码。

7. The test case can be seen in /generated_projects. All the project in it can be run directly.
7. 测试案例在文件夹generated_projects里，文件夹里的代码都可以直接运行。