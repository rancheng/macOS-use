<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./static/browser-use-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="./static/browser-use.png">
  <img alt="Shows a black Browser Use Logo in light color mode and a white one in dark color mode." src="./static/browser-use.png"  width="full">
</picture>

<br/>

<!-- [![GitHub stars](https://img.shields.io/github/stars/gregpr07/browser-use?style=social)](https://github.com/gregpr07/browser-use/stargazers) -->
[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)
<!-- [![Documentation](https://img.shields.io/badge/Documentation-📕-blue)](https://docs.browser-use.com) -->
[![Twitter Follow](https://img.shields.io/twitter/follow/OfirOzeri?style=social)](https://x.com/OfirOzeri)
<br>
<div align="center">
  <h3>Developed by <a href="https://github.com/eDeveloperOZ">Ofir Ozeri</a> </h3>
</div>
Enable AI to control your MacBook apps(Soon: iPhone, iPads) 🤖.
<br>
mlx-use is a project built on Browser-use agent services and allows the AI agent to interact with every app from the Apple framework

# Our Vision:
TLDR: Tell every Apple device what to do, and it gets it done, on EVERY APP.
<br><br>
This project aimes to be build the AI agent of the MLX framework by Apple that would allow the agent to prefrom any action on an Apple device. Our final goal is a open source library that anyone can clone, powered by the [mlx](https://github.com/ml-explore/mlx) and [mlx-vlm](https://github.com/Blaizzy/mlx-vlm) to run local private infrence at zero cost.


# Getting strated
⚠️ Please read the [Warning](#warning) first!<br>
clone the repo
```bash
git clone https://github.com/browser-use/macOS-use.git && cd macOS-use
```
Get an API from one of the supported providers [OAI]() [Anthropic]() or [Gemini]() and set it in the .env file
```bash
cp .env.example .env
```
<br>
We reccomand using mlx-use with uv environment
```bash
brew install uv && uv venv && ./.venv/bin/activate
```
Install locally and thasts it! your'w good to go! try the first exmaple!
```bash
uv pip install --eitable . && pytohn examples/try.py
```

# ⚠️ WARNING
This project is stil under developmeant and user discretion is advised!
mlx-use can and will use your private credetials to complete it's task, lunch and interact WITH EVERY APP and UI componant in your MacBook and restrictions are to model are still under active development! it is not recoammnded to operate it un-supervised YET
mlx-use WILL NOT STOP at captha or any other forms of bot identifications, so once again, user discretion is advised.


# Demos
## click for full video
[prompt](https://github.com/browser-use/macOS-use/blob/main/examples/calculate.py): Calculate how much is 5 X 4 and return the result, then call done.
[![calc-5-times-4](https://github.com/eDeveloperOZ/mlx-use/blob/main/static/calc-5-times-4.gif  "Click for full video")](https://x.com/OfirOzeri/status/1883110905665433681)

<br/><br/>

[prompt](https://github.com/browser-use/macOS-use/blob/main/examples/check_time_online.py): Can you check what hour is Shabbat in israel today? call done when you finish.
[![check-time-online](https://github.com/eDeveloperOZ/mlx-use/blob/main/static/check-time-online.gif  "Click for full video")](https://x.com/OfirOzeri/status/1883109604416278552)

<br/><br/>

[prompt](https://github.com/browser-use/macOS-use/blob/main/examples/login_to_auth0.py): Go to auth0.com, sign in with google auth, choose ofiroz91@gmail.com account, login to the website and call done when you finish.
[![login-to-auth0](https://github.com/eDeveloperOZ/mlx-use/blob/main/static/login-to-auth0.gif  "Click for full video")](https://x.com/OfirOzeri/status/1883455599423434966)

<br>
## Roadmap goals:
1. Support MacBooks at SOTA reliability 
- [ ] Refine the Agent prompting.
- [ ] Release the first working version to pypi.
- [ ] Improve self-correction.
- [ ] Add feature to allow the agent to check existing apps if failing, e.g. calendar app actual name is iCal.
- [ ] Add action for the agent to ask input from the user. 
- [ ] Test Test Test! and let us know what and how to improve!
2. Support local infrence with small fine tuned model
- [ ] Add support for infrence with local models using mlx and mlx-vlm
- [ ] Fine tune a small model that every device can run infrence with
- [ ] SOTA reliability.
3. Support iPhone/iPad
<br>
## Contributing

We are a new project and would love contributors! Feel free to PR, open issues for bugs or feature requests.

## Thanks
## Thanks

We would like to extend our heartfelt thanks to [![Twitter Follow](https://img.shields.io/twitter/follow/Gregor?style=social)](https://x.com/gregpr07) and [![Twitter Follow](https://img.shields.io/twitter/follow/Magnus?style=social)](https://x.com/mamagnus00) for their incredible work in developing Browser Use. Their dedication and expertise have been invaluable, especially in helping with the migration process. We couldn't have done it without you guys!












Browser use is the easiest way to connect your AI agents with the browser. If you have used Browser Use for your project feel free to show it off in our [Discord](https://link.browser-use.com/discord).

To learn more about the library, check out the [documentation 📕](https://docs.browser-use.com).

# Quick start

With pip:

```bash
pip install browser-use
```

install playwright:

```bash
playwright install
```

Spin up your agent:

```python
from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
load_dotenv()

async def main():
    agent = Agent(
        task="Go to Reddit, search for 'browser-use' in the search bar, click on the first post and return the first comment.",
        llm=ChatOpenAI(model="gpt-4o"),
    )
    result = await agent.run()
    print(result)

asyncio.run(main())
```

And don't forget to add your API keys to your `.env` file.

```bash
OPENAI_API_KEY=
```

For other settings, models, and more, check out the [documentation 📕](https://docs.browser-use.com).

### Test with UI

You can test [browser-use with a UI repository](https://github.com/browser-use/web-ui)

Or simply run the gradio example:

```
uv pip install gradio
```

```bash
python examples/gradio.py
```

# Demos

[Prompt](https://github.com/browser-use/browser-use/blob/main/examples/real_browser.py): Write a letter in Google Docs to my Papa, thanking him for everything, and save the document as a PDF.

![Letter to Papa](https://github.com/user-attachments/assets/242ade3e-15bc-41c2-988f-cbc5415a66aa)

<br/><br/>

[Prompt](https://github.com/browser-use/browser-use/blob/main/examples/find_and_apply_to_jobs.py): Read my CV & find ML jobs, save them to a file, and then start applying for them in new tabs, if you need help, ask me.'

https://github.com/user-attachments/assets/171fb4d6-0355-46f2-863e-edb04a828d04

<br/><br/>

Prompt: Find flights on kayak.com from Zurich to Beijing from 25.12.2024 to 02.02.2025.

![flight search 8x 10fps](https://github.com/user-attachments/assets/ea605d4a-90e6-481e-a569-f0e0db7e6390)

<br/><br/>

[Prompt](https://github.com/browser-use/browser-use/blob/main/examples/save_to_file_hugging_face.py): Look up models with a license of cc-by-sa-4.0 and sort by most likes on Hugging face, save top 5 to file.

https://github.com/user-attachments/assets/de73ee39-432c-4b97-b4e8-939fd7f323b3

## More examples

For more examples see the [examples](examples) folder or join the [Discord](https://link.browser-use.com/discord) and show off your project.

# Vision

Tell your computer what to do, and it gets it done.

## Roadmap
- [ ] Improve memory management 
- [ ] Enhance planning capabilities
- [ ] Improve self-correction
- [ ] Fine-tune the model for better performance
- [ ] Create datasets for complex tasks
- [ ] Sandbox browser-use for specific websites
- [ ] Implement deterministic script rerun with LLM fallback
- [ ] Cloud-hosted version
- [ ] Add stop/pause functionality
- [ ] Improve authentication handling
- [ ] Reduce token consumption
- [ ] Implement long-term memory
- [ ] Handle repetitive tasks reliably
- [ ] Third-party integrations (Slack, etc.)
- [ ] Include more interactive elements
- [ ] Human-in-the-loop execution
- [ ] Benchmark various models against each other
- [ ] Let the user record a workflow and browser-use will execute it
- [ ] Improve the generated GIF quality
- [ ] Create various demos for tutorial execution, job application, QA testing, social media, etc.


## Contributing

We love contributions! Feel free to open issues for bugs or feature requests.

## Local Setup

To learn more about the library, check out the [local setup 📕](https://docs.browser-use.com/development/local-setup).

## Cooperations
We are forming a commission to define best practices for UI/UX design for browser agents. 
Together, we're exploring how software redesign improves the performance of AI agents and gives these companies a competitive advantage by designing their existing software to be at the forefront of the agent age. 

Email [Toby](mailto:tbiddle@loop11.com?subject=I%20want%20to%20join%20the%20UI/UX%20commission%20for%20AI%20agents&body=Hi%20Toby%2C%0A%0AI%20found%20you%20in%20the%20browser-use%20GitHub%20README.%0A%0A) to apply for a seat on the committee. 

## Citation

If you use Browser Use in your research or project, please cite:

```bibtex
@software{browser_use2024,
  author = {Müller, Magnus and Žunič, Gregor},
  title = {Browser Use: Enable AI to control your browser},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/browser-use/browser-use}
}
```

---

<div align="center">
  Made with ❤️ in Zurich and San Francisco
</div>

[Email me](mailto:tobi@browser.use?subject=I%20want%20to%20join%20the%20UI/UX%20commission%20for%20AI%20agents&body=Hi%20Toby%2C%0A%0AI%20found%20you%20in%20the%20browser-use%20GitHub%20README.%0A%0A)
