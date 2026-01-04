todo

separate prompt with ONLY with resizing gutters, single page, use 5 placeholder images? Try it 5x different ways. Find a way without explicit pixels.


define the default crop behavior x,y,width,height better

learn more about cropping parameters (via AI)
I guess there is some redundancy in having both focalPoint and the full set of crop_x?

write the mathical functions together with tests
- changing layouts
- resizing based on changing the gutter

and let the main project use this CORE without having to rewrite it every single time
(and/or extract it from a couple of generated index.html files via AI -> take the best parts) and just instruct the AI to use it (saying which high level interface it has)


- modal doesn't close
- changing layout creates wrong
- ask if we are reinventing the wheel somewhere and should use a lib
- send fotofabriek email with requirements for PDF
- check if fabric could
- do a standalone demo with croppy?
- croppy without modal if possible


better in previous
- auto snap logic
- cannot resize either hor or ver

1 page layout has no 1cm margin

for simplicity decided to only handle the spread pages, but the final result should also include a first and last page (with full picture then).

Can create another standalone app that just adds 2 pages to an existing PDF.. or creates a different first-last.json (which the pdf generator can use)