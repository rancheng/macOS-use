<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./static/browser-use-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="./static/browser-use.png">
  <img alt="Shows a black Browser Use Logo in light color mode and a white one in dark color mode." src="./static/browser-use.png"  width="full">
</picture>

<br/>

<!-- [![GitHub stars](https://img.shields.io/github/stars/gregpr07/browser-use?style=social)](https://github.com/gregpr07/browser-use/stargazers) -->
[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)
[![Twitter Follow](https://img.shields.io/twitter/follow/OfirOzeri?style=social)](https://x.com/OfirOzeri)
<br>
<div align="center">
  <h3>Developed by <a href="https://github.com/eDeveloperOZ">Ofir Ozeri</a> </h3>
</div>
Enable AI to control your MacBook apps(in the future: iPhone, iPads) 🤖.
<br>
mlx-use is a project built on Browser-use agent services and allows the AI agent to interact with every app from the Apple framework

# Our Vision:
TLDR: Tell every Apple device what to do, and it gets it done, on EVERY APP.
<br><br>
This project aimes to be build the AI agent of the MLX framework by Apple that would allow the agent to prefrom any action on an Apple device. Our final goal is a open source library that anyone can clone, powered by the [mlx](https://github.com/ml-explore/mlx) and [mlx-vlm](https://github.com/Blaizzy/mlx-vlm) to run local private infrence at zero cost.


# Getting strated
⚠️ Please read the [Warning](#warning) first!<br><br>

Clone the repo
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
## Click for full video
[prompt](https://github.com/browser-use/macOS-use/blob/main/examples/calculate.py): Calculate how much is 5 X 4 and return the result, then call done. <br>
[![calc-5-times-4](https://github.com/eDeveloperOZ/mlx-use/blob/main/static/calc-5-times-4.gif  "Click for full video")](https://x.com/OfirOzeri/status/1883110905665433681)

<br/><br/>

[prompt](https://github.com/browser-use/macOS-use/blob/main/examples/check_time_online.py): Can you check what hour is Shabbat in israel today? call done when you finish. <br>
[![check-time-online](https://github.com/eDeveloperOZ/mlx-use/blob/main/static/check-time-online.gif  "Click for full video")](https://x.com/OfirOzeri/status/1883109604416278552)

<br/><br/>

[prompt](https://github.com/browser-use/macOS-use/blob/main/examples/login_to_auth0.py): Go to auth0.com, sign in with google auth, choose ofiroz91@gmail.com account, login to the website and call done when you finish. <br>
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
2. Support local infrence with small fine tuned model.
- [ ] Add support for infrence with local models using mlx and mlx-vlm.
- [ ] Fine tune a small model that every device can run infrence with.
- [ ] SOTA reliability.
3. Support iPhone/iPad

<br>

## Contributing

We are a new project and would love contributors! Feel free to PR, open issues for bugs or feature requests.

## Thanks

We would like to extend our heartfelt thanks to [![Twitter Follow](https://img.shields.io/twitter/follow/Gregor?style=social)](https://x.com/gregpr07) and [![Twitter Follow](https://img.shields.io/twitter/follow/Magnus?style=social)](https://x.com/mamagnus00) for their incredible work in developing Browser Use. Their dedication and expertise have been invaluable, especially in helping with the migration process. We couldn't have done it without you guys!

