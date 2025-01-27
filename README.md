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
  <h2><a href="#our-vision">Command your MacBook, and it's done—across EVERY app.</a><br>
  Created by <a href="https://github.com/eDeveloperOZ">Ofir Ozeri </a><br> 
   </h2>
</div>

<br>

mlx-use enables AI agents to interact with Apple framework applications through browser-use agent tech [see it in action!](#demos)

# Quick start
⚠️ Important: Review the [Warning](#warning) section before proceeding. <br> 

Clone first
<br>

```bash
git clone https://github.com/browser-use/macOS-use.git && cd macOS-use
```
Don't forget an API <br>Supported providers: [OAI](https://platform.openai.com/docs/quickstart), [Anthropic](https://docs.anthropic.com/en/api/admin-api/apikeys/get-api-key) or [Gemini](https://ai.google.dev/gemini-api/docs/api-key) (deepseek R1 coming soon!) and set it in the .env file

<br> At the moment, mlx-use works best with OAI or Anthropic API, tho Gemini is free. it works great two, just not as reliably. <br>

```bash
cp .env.example .env
```
We reccomand using mlx-use with uv environment
<br>

```bash
brew install uv && uv venv && ./.venv/bin/activate
```
Install locally and that'e good to go! try the first exmaple!
<br>

```bash
uv pip install --eitable . && pytohn examples/try.py
```

# Demos
<h3> Click the GIF for the full video! </h3>

[prompt](https://github.com/browser-use/macOS-use/blob/main/examples/calculate.py): Calculate how much is 5 X 4 and return the result, then call done. 

```bash
python exmaple/calculate.py
```

<br>

[![calc-5-times-4](https://github.com/browser-use/macOS-use/blob/main/static/calc-5-X-4.gif  "Click the GIF for full video!")](https://x.com/OfirOzeri/status/1883110905665433681)

<br/>

[prompt](https://github.com/browser-use/macOS-use/blob/main/examples/check_time_online.py): Can you check what hour is Shabbat in israel today? call done when you finish. 

```bash
python exmaple/check_time_online.py
```
<br>

[![check-time-online](https://github.com/browser-use/macOS-use/blob/main/static/check-time-online.gif  "Click for full video")](https://x.com/OfirOzeri/status/1883109604416278552)

<br/>

[prompt](https://github.com/browser-use/macOS-use/blob/main/examples/login_to_auth0.py): Go to auth0.com, sign in with google auth, choose ofiroz91 gmail account, login to the website and call done when you finish.

```bash
python exmaple/login_to_auth0.py
```

 <br>

[![login-to-auth0](https://github.com/browser-use/macOS-use/blob/main/static/login-to-auth0.gif  "Click for full video")](https://x.com/OfirOzeri/status/1883455599423434966)

<br>


# Our Vision:
TLDR: Tell every Apple device what to do, and it gets done. on EVERY APP.
<br><br>
This project aimes to build the AI agent of the MLX framework by Apple that would allow the agent to prefrom any action on any Apple device. Our final goal is a open source that anyone can clone, powered by the [mlx](https://github.com/ml-explore/mlx) and [mlx-vlm](https://github.com/Blaizzy/mlx-vlm) to run local private infrence at zero cost.

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

# WARNING

This project is stil under developmeant and user discretion is advised!
mlx-use can and will use your private credentials, [auth services](https://github.com/browser-use/macOS-use/blob/main/examples/login_to_auth0.py) or stored passwords to complete its task, launch and interact WITH EVERY APP and UI component in your MacBook and restrictions to the model are still under active development! It is not recommended to operate it unsupervised YET
mlx-use WILL NOT STOP at captha or any other forms of bot identifications, so once again, user discretion is advised.

## Disclamr:

As this is an early stage release, You might experience varying success rates depending on task prompt, we're actively working on improvements. <br> talk me on [X/Twitter](https://x.com/OfirOzeri) or contact me on [Discord](https://link.browser-use.com/discord), your input is crucial and highly valuable!<br>


## Contributing

We are a new project and would love contributors! Feel free to PR, open issues for bugs or feature requests.

## Thanks

I would like to extend our heartfelt thanks to [![Twitter Follow](https://img.shields.io/twitter/follow/Gregor?style=social)](https://x.com/gregpr07) and [![Twitter Follow](https://img.shields.io/twitter/follow/Magnus?style=social)](https://x.com/mamagnus00) for their incredible work in developing Browser Use. Their dedication and expertise have been invaluable, especially in helping with the migration process and I couldn't have done it without them!

