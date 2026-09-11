# Publishing the Robo Trade book

Source repository: [nutdnuy/robo-trade-notes](https://github.com/nutdnuy/robo-trade-notes). The Pages address is [nutdnuy.github.io/robo-trade-notes](https://nutdnuy.github.io/robo-trade-notes/); the first successful deployment makes the book available there.

The workflow in `.github/workflows/pages.yml` rebuilds and publishes the website whenever a commit reaches `main`. It can also be run manually from **Actions → Publish Robo Trade book → Run workflow**, selecting `main`.

## Initial repository setup

The book repository is configured to use **GitHub Actions** as its Pages source. For a new copy, select **Settings → Pages → Build and deployment → Source → GitHub Actions** and enable GitHub Actions if necessary. The workflow creates a `github-pages` deployment environment and reports the published URL there. [GitHub publishing-source documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

No Webull credentials, personal access token, or user-created repository secret is needed by this workflow. Deployment uses GitHub's automatically provided token and OIDC identity. Initial Pages enablement is a repository setting; the workflow does not attempt to enable it with a personal token. [Official Pages workflow requirements](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [configure-pages inputs](https://github.com/actions/configure-pages/blob/v5/action.yml)

## What is built and published

The Ubuntu build job sets up **Node.js 22** and **Python 3.12**, then runs:

```shell
npm ci
npm test
npm run build:pages
```

The build generates the book configuration from `_config.yml` and `_toc.yml`, validates content, prepares downloads, and creates the standalone website. **The publish directory is `_site/`**, containing `index.html`, `chapter-01.html` through `chapter-10.html`, local assets, and downloads. Only that directory is uploaded as the Pages artifact. The deployment job runs only after a successful build and only from `main`.

Edit Markdown in `content/`, book settings in the YAML files, and appearance in `book.css`; commit those sources to update the public site. Generated `_site/` HTML does not need to be committed. Relative links also work when GitHub hosts the book beneath a repository path, such as `/robo-trade-notes/`.

The Python build step only packages files using the standard library (`pathlib`, `json`, and `zipfile`). CI distributes the notebooks with their saved outputs; it does not execute notebook cells, install pandas/Jupyter/Webull, or connect to a brokerage account. When changing Python lesson logic, run its notebook checks locally before committing refreshed outputs.

## Checking a deployment

Open the workflow run in **Actions**. Both build and deploy must be green. Use its `github-pages` URL, then check a direct chapter link such as `chapter-05.html#drawdown`. If Pages configuration fails, verify that the publishing source is **GitHub Actions**; if a build fails, open the failing step before retrying. A failed build does not deploy its output.

Official action versions checked on 11 September 2026: [checkout v7](https://github.com/actions/checkout/blob/v7/action.yml), [setup-node v7](https://github.com/actions/setup-node/blob/v7/action.yml), [setup-python v7](https://github.com/actions/setup-python/blob/v7/action.yml), [configure-pages v5](https://github.com/actions/configure-pages/blob/v5/action.yml), [upload-pages-artifact v4](https://github.com/actions/upload-pages-artifact/blob/v4/action.yml), and [deploy-pages v4](https://github.com/actions/deploy-pages/blob/v4/action.yml). These are official major-version tags; review this file and the workflow when upgrading them.
