<p align="center">
  <img src="https://raw.githubusercontent.com/iteranya/anita-cms/main/docs/anitacms.png" alt="Anita CMS Logo" width="512">
  <br><br>
  <a href="https://www.gnu.org/licenses/agpl-3.0">
    <img src="https://img.shields.io/badge/License-AGPL_v3-blue.svg" alt="License: AGPL v3">
  </a>
  <!-- Added Version Badge -->
  <a href="https://github.com/iteranya/anita-cms/releases">
    <img src="https://img.shields.io/badge/Version-0.73-brightgreen.svg" alt="Version 0.38">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.12+-yellow.svg" alt="Python">
  </a>
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/Framework-FastAPI-009688.svg" alt="FastAPI">
  </a>
  <a href="https://pocketbase.io/">
    <img src="https://img.shields.io/badge/Pocketbase-Integrated-blue?logo=pocketbase" alt="SQLAlchemy">
  </a>
</p>
<h1 align="center">Anita TARDIS Edition - It's Smaller On The Outside</h1>
<h2 align="center">WORK IN PROGRESS</h2>

---

## What is Anita - TARDIS Edition

Anita is a Web Framework designed for extreme simplicity. It is designed so that even a complete amateur with zero days of Web Development can create a website. It is smaller on the outside, it can run on a potato and powerful enough to handle a stupid amount of traffic.  

### Why????

- This version of Anita is designed by an actual highschool teacher
- It is designed in terms of: "Oh god this is gonna be a nightmare to teach isn't it?"
- It is created to be as simple as possible and as basic as possible
- It is hackable to the point of absurdity, using a very, very, very strict domain-based architecture
- Expanding on it is also trivial due to this.

## Features

Anita come with a bunch of feature out of the box. Just enough to get you started to make your website but not too much that it makes you question your life choices. (why the hell do you even need SEO this day and age?)

### Admin Page

Anita comes with an Admin Page to manage your Pages, your Collections, your Users, and your Configs. That is all. You can add more if you like, it's very easy, and you literally do NOT need to touch the core features. That's what Domain Architecture look like (why the hell did I use Layer Architecture again??? Oh right, my last project was a discord bot)

### Collection

Anita just acts as a secondary thin layer between Pocketbase and client request. She replaces the Pocketbase Admin by bringing in additional security checks. Funny enough, you can skip this and head straight to Pocketbase Admin Page. But then you'll have to handle auth yourself.

### Article

Unlike the old Anita, we decoupled the Markdown Page from the HTML Page. Why? WHY NOT?! WHY DIDN'T WE DO THIS BEFORE?!?!?!?

Ahem, anyway, yeah, markdown stuff goes here. HTML stuff goes to pages. Different table, different collection, very simple, very nice. Web template to render markdown goes to pages too btw. Yeah...

### HTML

We store HTML file the same way we store article. With a few field to toggle off / on the 'use main site header' thing. Yknow, if you actually have site header. Which I should have... Hmmm... Anyway, there it is, just like Markdown.

### Pages

Anita's specialty is that she stores custom pages inside her own database. In this case, the database is kept inside of Pocketbase Page Collection instead of SQL Alchemy. Anita only handles the security management at front, Pocketbase handles everything else. Anita will route page based on the permissions and labels, these labels then determine the page slugs and site map schema and who can access which pages.

The Pages collection does not contain the HTML / Markdown. You have to link a page with the corresponding Article and HTML to render it. Pages is completely and 100% only contain metadata. And yes of course, they are way, way, way lighter to sort through and such.

### User

Anita comes with a granular Discord-like ABAC - RBAC. Though a user is limited to only one role. This ABAC is designed so that you can always create a specific permission for your user. Like who can create new article and web page and more.

### Aina

Aina is now dead simple, left side, Ace Editor for HTML, right side, an iFrame. That's it, an HTML viewer and editor. Also a toggle to save draft, to publish, and to use the template thing or just render the html raw as is. Oh and I have an upcoming project of the same name because Aina is a heckin cute name.

### Asta

Still milkdown still works decently~ Not much to say about Asta, she's great as she is. You can't get any simpler than a markdown.

## Architecture

### FastAPI

A dead simple FastAPI server, sorta

### HTMX

HTMX is used for the 'templating'... Goddammmit, what is it called when you have Header and Footer and just want to shove something between it without thinking too hard about it again??? Ah whatever, it also does the Admin Page thing. I do hybrid. HTMX for the overall page and...

### Alpine

Alpine for everything else. Like... modals and html and whatever...

### Pocketbase

SQL Alchemy is great because you can move to Postgres. But then I realized that Postgres is literally overkill for... my target audience. If you ever found yourself thinking "Oh god, but what if Pocketbase can't handle my traffic", then you are looking at the wrong tech stack or delusional. Because buddy, no, you need to be extremely lucky to find the limit of Pocketbase.


## What about the original Anita?

Shelved, most likely, since no one is using it as far as I know. (Thank god for that).

Anyway, with Pocketbase, the API should be a little bit more bearable. Have fun then, see ya~

#### PS: License does not change, still AGPL-3, and that PLEDGE.MD is NOT going anywhere.