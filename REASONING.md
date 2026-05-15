# Reasoning & Design Choices

## 1. Why PostgreSQL

I chose PostgreSQL because I was already familiar with it before this project. I knew how it worked, how to connect to it, and how to navigate it through pgAdmin, so it made sense to use something I could trust rather than learn a new database at the same time as learning FastAPI.

---

## 2. How I modelled the M:N relationship

To understand the relationships between tables before writing any code, I used [dbdiagram.io](https://dbdiagram.io) to visualise the schema. This made it much easier to see how everything connected.

For books and authors, I used a Many-to-Many, relationship because a single book can have more than one author, and a single author can have written more than one book. The `book_authors` table acts as a bridge between the two it holds a `book_id` and an `author_id`, and together they form a composite primary key. Without this junction table, there would be no clean way to represent that relationship.

---

## 3. How I avoided N+1 queries in the search endpoint

In the book search endpoint, I used `joinedload` from SQLAlchemy. Without it, every time the API returned a list of books and tried to access each book's authors, it would fire a separate query per book that's the N+1 problem.

With `joinedload(Book.authors)`, SQLAlchemy fetches the books and their authors in a single query, so no matter how many books come back, it's still just one database call.

---

## 4. Why DELETE with active loans returns 409

The system should not allow deleting a member or book that has an active loan. If a member is deleted while they still have a book checked out, the loan record becomes orphaned it points to a member that no longer exists, and there's no way to know who has the book.

Returning 409 Conflict makes this explicit: the request is valid, but the current state of the system won't allow it. The right flow is to return the book first, then delete the member.

---

## 5. How I structured the test suite

I have not implemented this feature into the project yet.
---

## 6. Scope choices

I completed most of the assessment the data model, all the main endpoints, filtering, pagination, the search endpoint, reports, Docker, Alembic, and API key authentication.

The one thing I left out is a more complete automated test suite. I haven't finished the testing section of my Udemy course yet, so rather than copy-paste tests I didn't fully understand, I wrote the ones I could genuinely explain. When I finish that section, I plan to come back and add proper coverage across the whole project.

About 90% of the code in this project I can read, explain, and defend. I used AI (mainly Claude) during the process, mostly to understand concepts, check my logic, and unblock myself when stuck. The first members endpoint I built together with AI while asking questions about everything. After that, I wrote the rest of the routers mostly on my own, only going back to AI or the members file when I got stuck or wanted to check something. I also used the FastAPI documentation for reference, mostly reading rather than copying.

---

## 7. External resources used

- [dbdiagram.io](https://dbdiagram.io) — for visualising and planning the database schema
- [FastAPI documentation](https://fastapi.tiangolo.com) — mainly for reference on routing, dependencies, and request handling
- Udemy course on FastAPI — the foundation for most of the structure used here
- Claude (Anthropic) — used throughout the project for explanations, debugging, and as a sounding board when stuck. All AI usage is documented honestly above.


The prompt I sent to Claude AI to generate this reasoning.md mainly the structure because I answered all the questions in the assessment truly myself
--------------------------------------------------------------------------
AI PROMPT: 
IMPORTANT RULES:
- Do NOT rewrite my thoughts or change my writing style.
- Keep the wording, tone, and explanations as close as possible to the original.
- Only fix small grammar, character, punctuation, and formatting issues where necessary.
- Organize the text into proper markdown sections and headings.
- Use clean markdown formatting (#, ##, bullet points, numbered lists, code formatting if needed).
- Make the document look professional and readable.
- Keep all technical explanations intact.
- Preserve the personal reasoning and implementation explanations.
- If some numbering is inconsistent, fix it.
- If some sentences are too long, split them without changing meaning.
- Rewrite everything in the english language
  -[ 
    Kam zgjedhur PostgreSQL si databazë për këtë projekt pasi që kam punuar edhe më herët me këtë databazë, andaj edhe e kam përdorur pasi që e di se si funksionon.

    Për lidhjen mes tabelave të databazës kam përdorur një web faqe që lejon vizualizimin e tabelave: https://dbdiagram.io/, që e ka bërë edhe më të lehtë të kuptoj lidhjen mes tyre, p.sh. tek book_author ka qenë si një urë lidhëse mes tabelave books dhe authors, pra duke marrë book id nga books dhe author id nga author ke mundur të shfaqësh librin me atë autor. Është përdorur M:N (many to many) për shkak se një autor mund të ketë shumë libra, por edhe një libër mund të ketë më shumë se 1 autor.


    Për t’iu shmangur n+1 queries për search endpoint kam përdorur joinedload, pra me joinedload me një query p.sh. kam marrë 2 të dhëna që më janë dashur për një member p.sh.


    Pasi që logjika e sistemit nuk e lejon që të kthejë 200 për shkak se nuk mund të fshish një member nëse ai ka active loan, përndryshe do të humbje gjithmonë atë libër, pasi që nuk do ta dije kush e ka huazuar. Prandaj kthen 409 duke i treguar perdoruesit se kerkesa qe po dergon funksionon pra (delete) por nuk e lejon sistemi.


    Kam përfunduar shumicën e detyrës, ajo çka kam lënë jashtë janë testimet automatike, për arsye se në kurs të Udemy akoma nuk e kam përfunduar section e unit & automation testing, por edhe pse nuk e kam bërë tani, gjatë këtij vikendi kur ta përfundoj kursin do t’i implementoj ato çka kam mësuar këtu. (Kam mundur të përdor AI për ta bërë, por nuk do të kuptoja asgjë. Nuk po them se nuk e kam përdorur AI gjatë kësaj detyre, por 90% të kodit e kuptoj dhe e di si funksionon dhe jam në gjendje ta shpjegoj si funksionon).


    Lista e resurseve të përdorura: së pari për databazë kam përdorur dbdiagram.io, për një vizualizim të tabelave, pastaj një ndihmesë ka qenë edhe pjesa e kursit në Udemy, tek pjesa e routers, API endpointave. Gjithashtu kam përdorur edhe AI siç e ceka më lart. Zakonisht mënyra se si e kam përdorur është: së pari me AI kam përfunduar endpoint-in e parë të members, por duke e pyetur për çdo gjë dhe me qëllim të kuptimit, pastaj pjesën tjetër të endpoints i kam bërë 85-90% vetë. Vetëm kur kam pasur ngecje ose kam kaluar tek file i members për të parë se ku kam gabuar ose jam drejtuar tek AI (Claude kryesisht). Gjithashtu kam përdorur edhe pak dokumentimin e FastAPI, kryesisht kam lexuar, nuk është që kam marrë ndonjë pjesë të gatshme të kodit.

]
--------------------------------------------------------------------------