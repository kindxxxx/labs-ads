# I. Doubly linked list

## Условие

Реализовать **двусвязный список** книг и выполнить команды. До `10^5` команд, последняя всегда `exit`.

| команда | действие | вывод |
|---------|----------|--------|
| `add_front title` | вставить в начало | `ok` |
| `add_back title` | вставить в конец | `ok` |
| `erase_front` | удалить первую | название или `error` |
| `erase_back` | удалить последнюю | название или `error` |
| `front` | посмотреть первую | название или `error` |
| `back` | посмотреть последнюю | название или `error` |
| `clear` | очистить список | `ok` |
| `exit` | конец | `goodbye` |

Если список пуст, `erase_*` / `front` / `back` печатают `error` и ничего не меняют. `clear` и `exit` работают и на пустом списке.

## Двусвязный список

У узла два указателя: `prev` и `next`. Дополнительно храним `head` и `tail`.

```
None <- A <-> B <-> C -> None
        ^head       ^tail
```

Вставка/удаление с **концов** тогда за `O(1)` — не надо идти с головы до хвоста.

## Идея операций

**add_front:** новый узел становится головой, его `next` — старая голова. Если список был пуст, хвост тоже этот узел.

**add_back:** симметрично с хвостом.

**erase_front:** запомнить значение головы, голова = `head.next`, у новой головы `prev = None`. Если голов не осталось — хвост тоже `None`.

**erase_back:** симметрично.

**clear:** в Python достаточно `head = tail = None` (узлы соберёт сборщик мусора).

## Сложность

каждая команда `O(1)`, всего `O(Q)`

## Пример по шагам

```
add_front Harry_Potter   [Harry_Potter]                 ok
add_back Light           [Harry_Potter, Light]          ok
erase_front              [Light]                        Harry_Potter
erase_back               []                             Light
erase_front              []                             error
add_front Happy          [Happy]                        ok
back                     [Happy]                        Happy
add_back Autumn          [Happy, Autumn]                ok
add_front Alchemy        [Alchemy, Happy, Autumn]       ok
clear                    []                             ok
front                    []                             error
exit                                                    goodbye
```
