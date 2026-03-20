local Colour = Var "Color"

local Colours = {
	["4th"]	= "4th",
	["8th"] = "8th",
	["12th"] = "12th",
	["16th"] = "16th",
	["24th"] = "24th",
	["32nd"] = "32nd",
	["48th"] = "48th",
	["64th"] = "64th",
	["192nd"] = "64th"
}

return Def.Model {
    Meshes=NOTESKIN:GetPath('','enchantmesh'),
    Materials=NOTESKIN:GetPath('_Down Tap Note '..Colours[Colour],'materials'),
    Bones=NOTESKIN:GetPath('','enchantmesh')
}



