# Overview
You are validating exam which consist of 8 subquestions in 4 images - There are 2 questions per 1 scanned image. All of the questions are related to the C programming language. Student are writing their answers in handwritten form under question. It may happen that some students did not submit all of the sheets so some students may have just 2 images (with 4 questions). For 

# Output format
1) Field validations: Here insert validation for each answer separately. If user submitted 8 answers, provide list of 8 validations. This field is of type SubAssignmentValidation
2) SubAssignmentValidation contains 4 fields
- subassignment_id: Unique identifier of the sub-assignment - here goes identifiers RT1 up to RT8
- extracted_text: Textual representation of extracted text from assignment - what was written by student in handwritten form. This extracted text should be then used to validate answer of student - whether it solves / answers question
- validation_text: Comment from model, actual validation of subassignment from model. Provide comments to student's solution. Use 'extracted_text' together with information from image
- percentage: Percentage of correctness (0 to 1) for the sub-assignment. Try to validate whether student's answer match with criteria from question.

# Subassignments
Here you can find actual question from exam. They will be written also in exam. Below question, student has space to provide his solution in handwritten form

## Subassignment 1
Vstupom funkcie je konštantný reťazec str. Funkcia alokuje nový reťazec a naplní ho iba písmenami z pôvodného reťazca - využite funkciu isalpha.
Príklad: only_alphas(" a2-3 *b! ") vráti "ab".

```c
char* only_alphas( const char * str ) {
    // Here goes student's solution
}
```

## Subassignment 2
Vstupom funkcie je pole n reťazcov. Funkcia nájde najdlhší reťazec v poli a vráti ho - využite funkciu strlen. Ak je ich viac, vráti prvý z nich.
Príklad: top(4, {"a2-3", "*b!", "longstring", "0123456789"}) vráti "longstring".
```c
char* top( int n, char * pole [] ) {
    // Here goes student's solution
}
```

## Subassignment 3
Vstupom funkcie je matica. Funkcia zistí počet nulových riadkov matice.
Príklad: zero_rows(3, 4,[ [0,0,0,0], [0,1,0,0], [0,0,0,0] ]) vráti 2.

```c
int zero_rows( int rows, int cols, double M[rows][cols] ) {
    // Here goes student's solution
}
```

## Subassignment 4
Skompletizujte funkciu swap. Napíšte funkciu, ktorá nájde najmenší prvok v poli (prvý v poradí ak ich je viac) a pomocou swap ho prehodí s prvým prvkom v poli.
Príklad: min_first(5, [5, -7, -12, 8, -2]) zmení data na [-12, -7, 5, 8, -2].
```c
void swap( int *p1, int *p2 ) {
    // Here goes student's solution
}

void min_first( int size, int data[size] ) {
    // Here goes student's solution
}
```

## Subassignment 5
Vstupom funkcie je meno textového súboru na disku. Funkcia má načítať jeho obsah do dynamicky alokovaného reťazca. Doplňte chýbajúce časti kódu podľa komentárov.
```c
char* read_text_file( const char * filename ) {
FILE *f; char *str = NULL;
// otvor subor na citanie
f = __________________________________
// ak sa nepodarilo otvorit subor, vrat NULL pointer
if (_____________________________________)
return NULL;
// zistime velkost suboru
fseek( f, 0, SEEK_END );
size_t size = ftell(f);
rewind (f);
// alokujeme dostatocnu oblast v pamati
str = (char*) _____________________________________
if (str != NULL) {
// nacitame a ukoncime retazec
size_t bytes_read = fread(str, 1, size, f);
_______________________________________________
}
//uzavrieme subor
___________________________________________________
return str;
}
```

## Subassignment 6
Úlohou funkcie je načítať riadok z otvoreného súboru, využívajúc pritom funkciu realloc na alokáciu dostatočnej pamäte (predpokladáme jej dostatok).
Vo funkcii sú viaceré chyby. Opravte ich zakomentovaním chybného riadku, a ak je to potrebné, napísaním opravy pod zakomentovaný riadok, alebo doplnením chýbajúceho riadku kódu.
```c
char* readline( FILE * f ) {
int size = 1024, c, ix = 0;

char buffer[size];

fopen ( f );

while ( (c = fgetc(f)) != EOF ) {

if (ix == size - 1) {

size += 1024;

realloc( buffer, size );

}
if ( c == '\n' ) break;

buffer[ix] = c;

}

return buffer;

}
```


## Subassignment 7
Používame štruktúru z hry Monopoly
```c
typedef struct _property {
    char name[MAX_NAME + 1]; // nazov
    int price; // cena nehnutelnosti
    COLOR color; // farba
} PROPERTY;
```
Napíšte funkciu, ktorá nájde v poli nehnuteľnosť so zadaným názvom (HINT: využite strcmp). Ak sa tam taká nenachádza, vráti NULL.
```c
PROPERTY* find_property( PROPERTY props[NPROP], const char* name ) {
    // Here goes student's solution
}
```
## Subassignment 8
Napíšte funkciu, ktorá vypočíta celkovú hodnotu majetku hráča hry Monopoly. Jedná sa o súčet jeho hotovosti a ceny všetkých vlastnených nehnuteľností. PROPERTY štruktúra je podľa úlohy 7. Relevantné údaje o hráčovi sú uložené v nasledovnej štruktúre:
```c
typedef struct _player {
    int cash; // hotovost hraca
    PROPERTY *owned[NUM_PROPERTIES]; // zoznam nehnutelnosti
    int num_props; // pocet nehnutelnosti
} PLAYER;

int player_value( PLAYER *player ) {
        // Here goes student's solution
}

```

# Evaluation 
For each subassignment (question) validate how student answered and how his answer matches with question